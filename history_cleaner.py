"""
Discord History Cleaner v0.1.0

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

BASE_URL = "https://discord.com/api/v9/channels/"


def get_channel_messages_endpoint(channel_id: str) -> str:
    """Returns the Discord's channel messages endpoint (full URL)"""
    return f"{BASE_URL}{channel_id}/messages"


def get_message_query_url(channel_id: str, before_message_id: str = None) -> None:
    """Return the URL for querying Discord messages with limit 100 and a "before-message" ID"""
    url = f"{get_channel_messages_endpoint(channel_id)}?"
    if before_message_id is not None:
        url += f"before={before_message_id}&limit=100"
    else:
        url += "?limit=100"
    return url


def get_channel_message_ids(
    cookie: str,
    auth_header: str,
    author_id: str,
    channel_id: str,
    message_id_start: str = None,
    message_id_stop: str = None,
) -> list[str] | None:
    """Returns a list of all the message IDs found in a particular channel id"""

    headers = BASE_HEADERS.copy()
    headers["Cookie"] = cookie.encode("latin-1", errors="ignore").decode("latin-1")
    headers["Authorization"] = auth_header

    before_message_id = message_id_start

    message_ids = []

    can_stop = False
    while not can_stop:
        res = http_get(
            get_message_query_url(channel_id, before_message_id),
            headers=headers,
            timeout=10,
        )
        if res.status_code != 200:
            break

        content = res.json()
        new_ids = [item["id"] for item in content if item["author"]["id"] == author_id]
        if not new_ids:
            break

        message_ids.extend(new_ids)
        before_message_id = new_ids[-1]

        if message_id_stop is not None and message_id_stop in new_ids:
            print(f"\nReached stop message ({message_id_stop})")
            break

        print(f"\nTotal messages retrieved: {len(message_ids)}")

    new_msg_ids = message_ids
    if message_id_stop is not None:
        new_msg_ids = []
        for msg_id in message_ids:
            new_msg_ids.append(msg_id)
            if msg_id == message_id_stop:
                break
    return new_msg_ids if message_id_start is None else [message_id_start] + new_msg_ids


def perform_channel_message_deletion(
    cookie: str, auth_header: str, channel_id: str, message_id: str
) -> None:
    """Perform an HTTP DELETE request to delete a message in channel,
    using `channel_id` and `message_id`"""

    url = f"{get_channel_messages_endpoint(channel_id)}/{message_id}"

    headers = BASE_HEADERS.copy()
    headers["Cookie"] = cookie.encode("latin-1", errors="ignore").decode("latin-1")
    headers["Authorization"] = auth_header

    res = http_delete(url, headers=headers, timeout=10)

    if res.status_code != 204:
        raise RuntimeError(
            f"\nError deleting message ({message_id}) in channel ({channel_id})"
            + f"\n\nHTTP Response:[{res.content}]"
        )


def _main() -> None:

    cookie = input("\nInsert your Discord cookie\n>>").strip()
    if not cookie:
        print("\nThis script needs a Discord Cookie in order to delete messages.")
        return

    auth_header = input(
        '\nInsert your Discord "Authentication Header" value\n>>'
    ).strip()
    if not auth_header:
        print("\nThis script needs also a Discord Authentication token.")
        return

    author_id = input("\nInsert your Discord User ID\n>>").strip()
    if not author_id:
        print("\nThis script needs your Discord User ID to delete your messages.")
        return

    channel_id = input(
        "\nInsert the Discord Channel ID to delete messages from\n>>"
    ).strip()
    if not channel_id:
        print("\nThis script needs also a Discord Channel ID.")
        return

    message_id_start = input(
        "\n(Optional) Insert the starting Message ID when searching channel messages"
        + "\nThis must be the ID of a message that you wrote."
        + "\n(Leave blank to start searching from the most recent message)\n>>"
    ).strip()
    if not message_id_start:
        message_id_start = None

    message_id_stop = input(
        "\n(Optional) Insert the stop Message ID"
        + "\nIt's the last message to look for when searching channel messages."
        + "\n(Leave blank to stop searching when reaching the last channel message)\n>>"
    ).strip()
    if not message_id_stop:
        message_id_stop = None

    message_ids = get_channel_message_ids(
        cookie,
        auth_header,
        author_id,
        channel_id,
        message_id_start=message_id_start,
        message_id_stop=message_id_stop,
    )
    if not message_ids:
        print(f"\nNo messages found in channel {channel_id}")

    print(f"\nFound {len(message_ids)} messages in channel ({channel_id})\n")

    for i, message_id in enumerate(message_ids):
        print(f"\nDeleting message ({i+1}/{len(message_ids)}):({message_id})")
        perform_channel_message_deletion(cookie, auth_header, channel_id, message_id)
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
