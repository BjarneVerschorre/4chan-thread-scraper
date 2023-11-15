# <img height=35 width=40 src="https://enthusiasms.org/wp-content/uploads/2018/10/4chan.png">4chan Thread Scraper
Scrapes an [4chan](https://4chan.org/) thread for attachments

## 🛠️ Requirements
This script uses [HTTPX](https://www.python-httpx.org/) to send HTTP requests asynchronously and needs to be installed. <br>
`pip3 install -r requirements.txt` to install all the requirements.

## 🖥️ How to use
To scrape a thread, use the `-u <URL>` or `--url <URL>` option. <br>
You can refresh (check for new ones) the attachments by using the `-r` or `--refresh` option.
```
usage: 4chan Thread Scraper [-h] [-u URL] [-r]

options:
  -h, --help         show this help message and exit.
  -u URL, --url URL  An 4chan thread URL to scrape.
  -r, --refresh      Looks through the attachments/ folder and redownloads any new attachments.
  -f FILE, --file FILE  A file containing 4chan thread urls to scrape.
```
