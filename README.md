# <img height=35 width=40 src="https://enthusiasms.org/wp-content/uploads/2018/10/4chan.png">4chan Thread Scraper
Scrapes an [4chan](https://4chan.org/) thread for attachments

## 🛠️ Requirements
This script uses [HTTPX](https://www.python-httpx.org/) to send HTTP requests asynchronously and needs to be installed. <br>
`pip3 install -r requirements.txt` to install all the requirements.

## 🖥️ How to use
Just run the script by doing `python main.py` while in the directory and it will ask you for an URL. <br>
The attachments will be saved in a (new) directory `attachments/<board>/<thread>`.
