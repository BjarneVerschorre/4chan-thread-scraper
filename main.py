import os
import re
import typing
import asyncio
import threading
import argparse
import httpx

# Constants
SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
REQUEST_TIMEOUT = 15

# Types
class URL(str):
    """ A string that represents a url """
    _REGEXES = {
        "short": re.compile(r'^(?:\/)?[a-zA-Z0-9]{1,3}\/thread\/\d{7,9}(?:\/)?$'),
        "thread": re.compile(r"^https?:\/\/boards\.4chan(?:nel)?\.org\/[a-zA-Z0-9]{1,3}\/thread\/\d{7,9}$"),
        "attachment": re.compile(r"^https?:\/\/i\.4cdn\.org\/[a-zA-Z0-9]{1,3}\/\d{16,18}(\.png|\.jpg|\.webm|\.jpeg|\.gif)$"),
        "data": re.compile(r"^https?:\/\/a\.4cdn\.org\/[a-zA-Z0-9]{1,3}\/thread\/\d{7,9}\.json$")
    }

    def __new__(cls, url:str):
        for regex in cls._REGEXES.values():
            if regex.match(url):
                return str.__new__(cls, url)
        raise ValueError(f"'{url}' is an invalid (4chan releated) url")


THREAD_POST = typing.TypedDict(
    "ThreadPost", 
    {
       "no": int,
       "com": str,
       "sub": typing.NotRequired[str],
       "tim": typing.NotRequired[int],
       "ext": typing.NotRequired[str],

    })
BOARD = typing.NewType("BOARD", str)
THREAD_DATA = typing.NewType("THREAD_DATA", dict)

# Argparse
parser = argparse.ArgumentParser(prog="4chan Thread Scraper")

parser.add_argument('-u', '--url', help='An 4chan thread URL to scrape', type=URL)
parser.add_argument('-r', '--refresh', action='store_true', help="Looks through the attachments/ folder and redownloads any new attachments.")
parser.add_argument('-f', '--file', help="A file containing 4chan thread urls to scrape", type=argparse.FileType('r'))

args = parser.parse_args()

# Functions
def get_thread_info(url:URL) -> tuple[BOARD, URL]:
    """ Returns the board and thread info url from a 4chan thread url """
    url_info = re.search(r"([a-zA-Z0-9]{1,3})\/thread\/(\d{7,9})", url)
    
    board = BOARD(url_info.group(1))
    thread_id = url_info.group(2)
    thread_info_url = URL(f"https://a.4cdn.org/{board}/thread/{thread_id}.json")

    return board, thread_info_url

def attachment_url(board:BOARD, filename:str) -> URL:
    """ Returns the url of an attachment from a board and filename """
    return URL(f"https://i.4cdn.org/{board}/{filename}")

def save_attachment(attachment_data: bytes, path:str, file_name: str):
    with open(f"{path}/{file_name}", "wb") as f:
        f.write(attachment_data)

    print(f"\rDownloaded \"{file_name}\"", end="")

async def download_attachment(client: httpx.AsyncClient, path:str, attachment_url:URL):
    try:
        res = await client.get(attachment_url, timeout=REQUEST_TIMEOUT)
    except (httpx.ReadTimeout, httpx.ConnectTimeout):
        print(f"Failed to download \"{attachment_url}\"")
        return

    if res.status_code != 200:
        print(f"Failed to download \"{attachment_url}\"")
        return
    
    file_name = attachment_url.split("/")[-1]
    threading.Thread(target=save_attachment, args=(res.content, path, file_name)).start()

async def main():
    if not args.url and not args.refresh and not args.file:
        parser.print_help()
        return
    
    thread_urls: list[URL] = []
    
    if args.url:
        thread_urls.append(URL(args.url))

    if args.refresh:
        for board in os.listdir(f"{SCRIPT_PATH}/attachments/"):
            for thread in os.listdir(f"{SCRIPT_PATH}/attachments/{board}/"):
                thread_url = f"https://boards.4chan.org/{board}/thread/{thread.split(' - ')[0]}"
                thread_urls.append(URL(thread_url))

    if args.file:
        for line in args.file.readlines():
            if not line.strip():
                continue
            thread_urls.append(URL(line.strip()))
    
    print(f"Found {len(thread_urls)} thread{'s' if len(thread_urls) != 1 else ''} to scrape.")

    for thread_url in thread_urls:

        # check if failed_threads.txt exists and has the thread url
        if os.path.isfile('failed_threads.txt'):
            with open('failed_threads.txt', 'r') as f:
                if thread_url in f.read():
                    continue

        board, thread_info_url = get_thread_info(thread_url)
        response = httpx.get(thread_info_url)

        if response.status_code != 200:
            print(f"Failed to get thread data from \"{thread_info_url}\"")

            with open('failed_threads.txt', 'a') as f:
                f.write(f"{thread_url}\n")

            continue

        thread_data:THREAD_DATA = response.json()

        initial_post:THREAD_POST = thread_data["posts"][0]
        thread_id:int = initial_post["no"]

        # Sanitize thread name for folder name
        thread_name:str = initial_post.get("sub", initial_post.get("com", "Unnamed thread"))
        thread_name = re.sub(r'<[^>]+>', ' ', thread_name).replace("/", " ")
        thread_name = re.sub(r'\s+', ' ', thread_name).strip()
        thread_name = re.sub(r"[\\\/:\*\?<>\|]", "", thread_name).strip()

        thread_name = thread_name[:50] + ' [...]' if len(thread_name) >= 50 else thread_name
    
        path = f"{SCRIPT_PATH}/attachments/{board}/{thread_id} - {thread_name}"
        print(f"\nScraping \"{thread_name}\"")

        thread_posts:list[THREAD_POST] = thread_data.get("posts", [])

        attachment_urls: list[URL] = []
        for post in thread_posts:
            if not "tim" in post or not "ext" in post:
                continue

            file_name = str(post["tim"]) + post["ext"]

            if os.path.isfile(f"{path}/{file_name}"):
                continue

            attachment_urls.append(attachment_url(board, file_name))

        print(f"Found {len(attachment_urls)} (new) attachment{'s' if len(attachment_urls) != 1 else ''}")

        os.makedirs(path, exist_ok=True)
        
        async with httpx.AsyncClient() as client:
            tasks = [download_attachment(client, path, attachment_url) for attachment_url in attachment_urls]
            await asyncio.gather(*tasks)

        # Wait until all threads are done
        for thread in threading.enumerate():
            if thread is threading.main_thread():
                continue
            if thread.name.startswith("asyncio_"):
                continue

            thread.join()
        
        print()

    print("Done")


if __name__ == "__main__":
   asyncio.run(main())   
