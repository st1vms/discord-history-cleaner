# discord-history-cleaner

Discord Self Bot for cleaning message history in a specific channel

## What is this?

This is a Discord Self-Bot that allows you to clear your message history in any Discord channel, public or even private. Uses your Discord Cookie and Discord Authentication token to perform the message deletions.

You can customize the deletion frequency and the message range in which to search for messages to delete.

## Requirements

- Python >= 3.10 Installed
- Python's `requests` library installed
- A Discord Cookie and Authentication Header
- Your Discord User ID
- The Channel ID to delete messages from

## How to use

Run the `history_cleaner.py` file and provide all the informations requested.

When prompted, you can also set two optional arguments, `Start Message ID` and `End Message ID`; the start message ID must be the ID of a message you have written that will be the first message to be deleted and from which previous messages will be searched; if left blank, the bot will start searching from the first message in the channel. The end message ID will be the last message to be searched, it can be a message written by someone else and will be used as a reference to stop searching for new messages to delete.

## DISCLAIMER

This self-bot is for personal and educational use only. It can delete your own message history in any Discord channel where you have permission. Be aware that self-bots violate Discord’s Terms of Service and using this may result in your account being banned. The creator is not responsible for any misuse or consequences resulting from the use of this tool.

## DONATING

A huge thank you in advance to anyone who would like to donate me a pizza Margherita :)

[![Buy Me a Pizza](https://img.buymeacoffee.com/button-api/?text=1%20Pizza%20Margherita&emoji=🍕&slug=st1vms&button_colour=0fa913&font_colour=ffffff&font_family=Bree&outline_colour=ffffff&coffee_colour=FFDD00)](https://www.buymeacoffee.com/st1vms)
