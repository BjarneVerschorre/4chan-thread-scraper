# 4chan-thread-scraper
 Scrape a 4chan thread for attachments

## Requirements
This script uses [httpx](https://www.python-httpx.org/) to send requests and needs to be installed. <br>
`pip3 install -r requirements.txt` to install all the requirements.

## How to use
Just run the script by doing `python main.py` while in the directory and it will ask you for an URL. <br>
The attachments will be saved in a (new) directory `attachments/<board>/<thread>`.
