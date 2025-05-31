"""
Discord History Cleaner v0.1.1

MIT License

Copyright (c) 2025 Stefano Raneri

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from time import sleep
from datetime import datetime
from requests import get as http_get
from requests import delete as http_delete

# Override the sleep amount in seconds between message deletions
DELETION_TIME_RATE_SECONDS = 1

# Override the User Agent, should be the same you use when accessing your Discord account
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:138.0) Gecko/20100101 Firefox/138.0"
)

# Override Base Headers
BASE_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "*/*",
    "Sec-GPC": "1",
    "Origin": "discord.com",
    "Host": "discord.com",
    "Alt-Used": "discord.com",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}

BASE_URL = "https://discord.com/api/v9"


def get_guild_search_endpoint(guild_id: str, channel_id: str, author_id: str) -> str:
    """Returns the Discord's guild search endpoint (full URL)"""
    return f"{BASE_URL}/guilds/{guild_id}/messages/search?author_id={author_id}&channel_id={channel_id}"


def get_channel_search_endpoint(channel_id: str, author_id: str) -> str:
    """Returns the Discord's channel search endpoint (full URL)"""
    return f"{BASE_URL}/channels/{channel_id}/messages/search?author_id={author_id}"


def get_delete_message_endpoint(channel_id: str) -> str:
    """Returns the Discord's channel messages endpoint for deletion (full URL)"""
    return f"{BASE_URL}/channels/{channel_id}/messages"


MESSAGE_ID_START_TIMESTAMP = 0
MESSAGE_ID_STOP_REACHED = False


def __do_search_messages(
    url: str,
    headers: dict[str, str],
    message_id_start: str = None,
    message_id_stop: str = None,
    offset: int = 0,
) -> tuple[list[str], int]:

    global MESSAGE_ID_START_TIMESTAMP
    global MESSAGE_ID_STOP_REACHED

    url = f"{url}&offset={offset}&include_nsfw=true"

    res = http_get(url, headers=headers, timeout=10)
    if res.status_code != 200:
        raise RuntimeError(f"[Code {res.status_code}]: {res.content}")

    data = res.json()

    message_ids = []

    total_results = data["total_results"]
    if total_results <= 0:
        return ([], 0)

    for message in data["messages"]:
        for item in message:
            # Check if we can start saving ids
            if (
                message_id_start is not None
                and MESSAGE_ID_START_TIMESTAMP == 0
                and item["id"] == message_id_start
            ):
                # Reached start message id
                MESSAGE_ID_START_TIMESTAMP = datetime.fromisoformat(
                    item["timestamp"]
                ).timestamp()

            if (
                message_id_stop is not None
                and not MESSAGE_ID_STOP_REACHED
                and item["id"] == message_id_stop
            ):
                MESSAGE_ID_STOP_REACHED = True
                message_ids.append(item["id"])

            if MESSAGE_ID_STOP_REACHED:
                # Reached stop message id
                return (message_ids, total_results)

            tmp = datetime.fromisoformat(item["timestamp"]).timestamp()
            if message_id_start is None or (
                MESSAGE_ID_START_TIMESTAMP != 0 and tmp <= MESSAGE_ID_START_TIMESTAMP
            ):
                message_ids.append(item["id"])

    return (message_ids, total_results)


def search_author_message_ids(
    cookie: str,
    auth_header: str,
    author_id: str,
    channel_id: str,
    guild_id: str = None,
    message_id_start: str = None,
    message_id_stop: str = None,
    is_dm: bool = True,
) -> list[str] | None:
    """Perform authenticated GET requests to /messages/ endpoint in order
    Returns a list of all the message IDs found in a particular `channel_id`,
    filtering by the provided `author_id`.

    `message_id_start` -> The first message wrote by `author_id` to delete and look for other messages from;
    leave None to start searching from the very first message.

    `message_id_stop` -> The last message to look for, also need to be a message wrote by `author_id`;
    leave None to stop looking for messages until the last message.
    """

    if is_dm:
        url = get_channel_search_endpoint(channel_id, author_id)
    else:
        url = get_guild_search_endpoint(guild_id, channel_id, author_id)

    headers = BASE_HEADERS.copy()
    headers["Cookie"] = cookie.encode("latin-1", errors="ignore").decode("latin-1")
    headers["Authorization"] = auth_header

    messages, total_results = __do_search_messages(
        url, headers, message_id_start=message_id_start, message_id_stop=message_id_stop
    )
    if not messages or total_results <= 0:
        return []

    current_results = len(messages)
    if current_results == total_results:
        return messages

    for offset in range(current_results, total_results, 25):
        messages.extend(
            __do_search_messages(
                url,
                headers,
                message_id_start=message_id_start,
                message_id_stop=message_id_stop,
                offset=offset,
            )[0]
        )
    return messages


def perform_channel_message_deletion(
    cookie: str, auth_header: str, channel_id: str, message_id: str, is_dm: bool = False
) -> None:
    """Perform an authenticated HTTP DELETE request to delete a message in public/private channel,
    requires a `channel_id` and a `message_id`"""

    url = f"{get_delete_message_endpoint(channel_id)}/{message_id}"

    headers = BASE_HEADERS.copy()
    headers["Cookie"] = cookie.encode("latin-1", errors="ignore").decode("latin-1")
    headers["Authorization"] = auth_header

    res = http_delete(url, headers=headers, timeout=10)

    if res.status_code != 204:
        try:
            count = float(res.json()["retry_after"]) + DELETION_TIME_RATE_SECONDS
            print(f"\nThe deletion rate limit was hit, retrying after {count} seconds...")
            sleep(count)
            
            http_delete(url, headers=headers, timeout=10)
        except Exception as e:
            raise RuntimeError(
                f"\nError deleting message ({message_id}) in guild/channel ({channel_id})"
                + f"\n{e}"
                + f"\n\nHTTP Response:[{res.content}]"
            )


def __ask_input(prompt: str, error_prompt: str = None) -> str | None:
    inp = input(prompt).strip().replace("\n", "")
    return inp if inp else print(error_prompt) if error_prompt is not None else None


def _main() -> None:

    cookie = __ask_input(
        prompt="\nInsert your Discord cookie\n>>",
        error_prompt="\nThis script needs a Discord Cookie in order to delete messages.",
    )
    if not cookie:
        return

    auth_header = __ask_input(
        prompt='\nInsert your Discord "Authentication Header" value\n>>',
        error_prompt="\nThis script needs also a Discord Authentication token.",
    )
    if not auth_header:
        return

    author_id = __ask_input(
        prompt="\nInsert your Discord User ID\n>>",
        error_prompt="\nThis script needs your Discord User ID to delete your messages.",
    )
    if not author_id:
        return

    is_dm = input("\nIs this a DM's Channel ID? (N/y)\n>>").lower().startswith("y")

    guild_id = None
    if is_dm:
        channel_id = __ask_input(
            prompt="\nInsert the Discord DM Channel ID to delete messages from\n>>",
            error_prompt="\nThis script needs a DM Channel ID.",
        )
        if not channel_id:
            return
    else:
        guild_id = __ask_input(
            prompt="\nInsert the Discord Guild ID to delete messages from\n>>",
            error_prompt="\nThis script needs a Guild ID.",
        )
        if not guild_id:
            return

        channel_id = __ask_input(
            prompt="\nInsert the Guild's Channel ID to delete messages from\n>>",
            error_prompt="\nThis script needs a Guild's Channel ID.",
        )
        if not channel_id:
            return

    message_id_start = __ask_input(
        prompt=f"\n(Optional) Insert the starting Message ID when searching {'DM Channel' if is_dm else 'Guild'} messages"
        + "\nThis must be the ID of a message that you wrote."
        + "\n(Leave blank to start searching from the most recent message)\n>>"
    )
    if not message_id_start:
        message_id_start = None

    message_id_stop = __ask_input(
        prompt="\n(Optional) Insert the stop Message ID"
        + f"\nIt's the last message to look for when searching {'DM Channel' if is_dm else 'Guild'} messages."
        + "\nThis also must be the ID of a message that you wrote."
        + f"\n(Leave blank to stop searching when reaching the last {'DM Channel' if is_dm else 'Guild'} message)\n>>"
    )
    if not message_id_stop:
        message_id_stop = None

    message_ids = search_author_message_ids(
        cookie,
        auth_header,
        author_id,
        channel_id,
        guild_id=guild_id,
        message_id_start=message_id_start,
        message_id_stop=message_id_stop,
        is_dm=is_dm,
    )
    if not message_ids:
        print(
            f"\nNo messages found in {'DM Channel' if is_dm else 'Guild'} {channel_id if is_dm else guild_id}"
        )
        return

    print(
        f"\nFound {len(message_ids)} messages in {'DM Channel' if is_dm else 'Guild'} ({channel_id if is_dm else guild_id})\n"
    )

    choice = (
        input("\nAre you sure you want to delete them? (N/y)\n>>")
        .strip()
        .lower()
        .startswith("y")
    )
    if not choice:
        print("\nQuitting...")
        return

    for i, message_id in enumerate(message_ids):
        print(f"\nDeleting message ({i+1}/{len(message_ids)}):({message_id})")
        try:
            perform_channel_message_deletion(
                cookie, auth_header, channel_id, message_id, is_dm=is_dm
            )
        except RuntimeError as e:
            print(f"{e}")
            return
        print(
            (
                f"\nMessage ({message_id}) deleted!"
                + f"\nSleeping {DELETION_TIME_RATE_SECONDS} seconds!"
            )
        )
        sleep(DELETION_TIME_RATE_SECONDS)

    print(f"\nDeleted {len(message_ids)} messages successfully!")


if __name__ == "__main__":
    _main()
