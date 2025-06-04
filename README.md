# discord-history-cleaner

Discord Self Bot for cleaning message history in a specific channel

## What is this?

Easily delete your own Discord messages from any channel (DM or guild) using this self-bot tool. 

Works with your account's session Cookie and Authentication token header and supports optional filtering by message range.

## Features

- Delete your own message history in any Discord channel (DM or Guild)
- Customizable deletion speed
- Optional filtering with Start/End message IDs

## Requirements

- Python 3.10 or newer
- `requests` Python package
- Your Discord **Cookie**, **Authorization Token**, and **User ID**
- The **Channel ID** (and optional **Guild ID**) to delete messages from


## How It Works

This script interfaces with Discord's public API endpoints using your account credentials.

It searches for messages authored by your user ID in a specified channel and deletes them one by one with a configurable delay.

> **Note:** The script does not use the official Discord bot API, as it is meant to operate as a self-bot.

## How To Use

1. Clone or download this repository.
2. Run `history_cleaner.py` in a terminal:

```shell
python history_cleaner.py
```

3. Follow the prompts:
    - Enter your:
        - Discord Cookie;
        - Authorization Token;
        - User ID.
    - Enter the Channel ID;
    - *(Optional)* Enter a Guild ID (for server channels, leave blank for DMs);
    - *(Optional)* Enter Start and Stop Message IDs to define deletion range.

- **Start ID**: The earliest message to begin searching from (not inclusive).
- **Stop ID**: The last message to stop searching at (not inclusive).

## Important Notes

- This script only deletes messages authored by your account.
- Start and Stop IDs are optional, but useful for fine-grained control.
- Make sure you input accurate credentials and IDs, otherwise the requests will fail.

## Legal Disclaimer

This self-bot is for personal and educational use only. It can delete your own message history in any Discord channel where you have permission. Be aware that self-bots violate Discord’s Terms of Service and using this may result in your account being banned. The creator is not responsible for any misuse or consequences resulting from the use of this tool.

## Donations

A huge thank you in advance to anyone who would like to donate me a pizza Margherita :)

[![Buy Me a Pizza](https://img.buymeacoffee.com/button-api/?text=1%20Pizza%20Margherita&emoji=🍕&slug=st1vms&button_colour=0fa913&font_colour=ffffff&font_family=Bree&outline_colour=ffffff&coffee_colour=FFDD00)](https://www.buymeacoffee.com/st1vms)
