VERSION_NUM = "0.1.3"

"""
Discord History Cleaner v0.1.3

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
    """
    Constructs the full Discord API URL to search messages by a specific author in a guild channel.

    Args:
        guild_id (str): The ID of the guild (server).
        channel_id (str): The ID of the channel within the guild.
        author_id (str): The ID of the author whose messages are being searched.

    Returns:
        str: Full URL for the guild message search endpoint.
    """
    return f"{BASE_URL}/guilds/{guild_id}/messages/search?author_id={author_id}&channel_id={channel_id}"


def get_channel_search_endpoint(channel_id: str, author_id: str) -> str:
    """
    Constructs the full Discord API URL to search messages by a specific author in a direct message (DM) channel.

    Args:
        channel_id (str): The ID of the DM channel.
        author_id (str): The ID of the author whose messages are being searched.

    Returns:
        str: Full URL for the channel message search endpoint.
    """
    return f"{BASE_URL}/channels/{channel_id}/messages/search?author_id={author_id}"


def get_delete_message_endpoint(channel_id: str) -> str:
    """
    Constructs the full Discord API URL to access or delete a specific message in a channel.

    Args:
        channel_id (str): The ID of the channel containing the message.

    Returns:
        str: Full URL for the message deletion endpoint.
    """
    return f"{BASE_URL}/channels/{channel_id}/messages"


def __do_search_messages(
    url: str,
    headers: dict[str, str],
    message_id_start: str = None,
    message_id_stop: str = None,
    offset: int = 0,
) -> tuple[list[str], int]:

    url = f"{url}&offset={offset}&include_nsfw=true"

    if message_id_start is not None:
        url += f"&max_id={message_id_start}"

    if message_id_stop is not None:
        url += f"&min_id={message_id_stop}"

    res = http_get(url, headers=headers, timeout=10)
    if res.status_code != 200:
        raise RuntimeError(f"[Code {res.status_code}]: {res.content}")

    data = res.json()

    total_results = data["total_results"]
    if total_results <= 0:
        return ([], 0)

    return (
        [item["id"] for message in data["messages"] for item in message],
        total_results,
    )


def search_author_message_ids(
    cookie: str,
    auth_header: str,
    author_id: str,
    channel_id: str,
    guild_id: str = None,
    message_id_start: str = None,
    message_id_stop: str = None,
    is_dm: bool = True,
) -> list[str]:
    """
    Searches for all messages authored by a specific user in a given Discord channel (guild or DM).

    Args:
        cookie (str): Discord session cookie.
        auth_header (str): Authorization token for Discord.
        author_id (str): ID of the author whose messages are to be found.
        channel_id (str): ID of the target channel.
        guild_id (str, optional): ID of the guild, required for non-DM channels. (Defaults to None).
        message_id_start (str, optional): ID of the first message to begin search from, this message won't be deleted. (Defaults to None).
        message_id_stop (str, optional): ID of the last message to stop at, this message won't be deleted. (Defaults to None).
        is_dm (bool, optional): Flag indicating if this is a DM channel. (Defaults to True).

    Returns:
        list[str]: List of message IDs matching the author in the channel.
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
    cookie: str, auth_header: str, channel_id: str, message_id: str
) -> None:
    """
    Deletes a specific message from a Discord channel (DM or guild).

    Args:
        cookie (str): Discord session cookie.
        auth_header (str): Authorization token for Discord.
        channel_id (str): ID of the channel containing the message.
        message_id (str): ID of the message to be deleted.

    Raises:
        RuntimeError: If the message deletion fails.
    """

    url = f"{get_delete_message_endpoint(channel_id)}/{message_id}"

    headers = BASE_HEADERS.copy()
    headers["Cookie"] = cookie.encode("latin-1", errors="ignore").decode("latin-1")
    headers["Authorization"] = auth_header

    res = http_delete(url, headers=headers, timeout=10)

    if res.status_code != 204:
        try:
            count = float(res.json()["retry_after"]) + DELETION_TIME_RATE_SECONDS
            print(
                f"\nThe deletion rate limit was hit, retrying after {count} seconds..."
            )
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
    print(f"\nDiscord History Cleaner v{VERSION_NUM}")
    print(
        "\nThis tool deletes your own messages from a specific Discord channel (guild or DM).\n"
    )

    cookie = __ask_input(
        prompt="\nEnter your Discord Cookie\n>>",
        error_prompt="\nThis script requires a Discord Cookie to delete your messages.",
    )
    if not cookie:
        return

    auth_header = __ask_input(
        prompt="\nEnter your Discord Authorization Token\n>>",
        error_prompt="\nThis script requires a Discord Authentication token to delete your messages.",
    )
    if not auth_header:
        return

    author_id = __ask_input(
        prompt="\nEnter your Discord User ID\n>>",
        error_prompt="\nThis script requires your Discord User ID to delete your messages.",
    )
    if not author_id:
        return

    channel_id = __ask_input(
        prompt="\nEnter the Discord Channel ID to delete messages from\n>>",
        error_prompt="\nThis script requires a Discord Channel ID.",
    )
    if not channel_id:
        return

    guild_id = __ask_input(
        prompt="\n(Optional) Enter the Guild ID if this is a guild channel (leave blank for DMs)\n>>",
    )
    is_dm = not bool(guild_id)

    message_id_start = __ask_input(
        prompt=f"\n(Optional) Enter Start Message ID, this message won't be deleted."
        + "\n(Leave blank to start searching from earliest message)\n>>"
    )

    message_id_stop = __ask_input(
        prompt="\n(Optional) Enter Stop Message ID, this message won't be deleted."
        + f"\n(Leave blank to scan up to latest message)\n>>"
    )

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
            f"\nNo messages found in {'DM Channel' if is_dm else 'Guild Channel'} {channel_id}"
        )
        return

    print(
        f"\nFound {len(message_ids)} messages in {'DM Channel' if is_dm else 'Guild Channel'} ({channel_id})\n"
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
                cookie, auth_header, channel_id, message_id
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
