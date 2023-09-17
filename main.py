import os
import re
import typing
import asyncio
import threading
import httpx

SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))



# Types
class URL(str):
    """ A string that represents a url """
    def __new__(cls, url:str):
        if not re.match(r"^https?://", url):
            raise ValueError("Invalid url")
        return str.__new__(cls, url)
    
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

def get_thread_info(url:URL) -> tuple[BOARD, URL]:
    """ Returns the board and thread info url from a 4chan thread url """
    a = re.match(r"https://boards.4chan.org/(\w+)/thread/(\d+)", url)
    if not a or len(a.groups()) != 2:
        raise ValueError("Invalid 4chan thread url")
    
    board = BOARD(a.group(1))
    thread_id = a.group(2)
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
    res = await client.get(attachment_url)

    if res.status_code != 200:
        print(f"Failed to download \"{attachment_url}\"")
        return
    
    file_name = attachment_url.split("/")[-1]
    threading.Thread(target=save_attachment, args=(res.content, path, file_name)).start()


async def main():
    thread_url = URL(input("4chan thread url: "))

    board, thread_info_url = get_thread_info(thread_url)
    thread_data:THREAD_DATA = httpx.get(thread_info_url).json()

    initial_post:THREAD_POST = thread_data["posts"][0]
    thread_id:int = initial_post["no"]

    # Sanitize thread name for folder name
    thread_name:str = initial_post.get("sub", initial_post.get("com", "Unnamed thread"))
    thread_name_match = re.match(r"[a-zA-Z0-9 -]+", thread_name)

    if thread_name_match:
        thread_name = thread_name_match.group(0)
    else:
        thread_name = "Unnamed thread"
 
    thread_posts:list[THREAD_POST] = thread_data.get("posts", [])

    attachment_urls = []
    for post in thread_posts:
        if not "tim" in post or not "ext" in post:
            continue
        attachment_urls.append(attachment_url(board, str(post["tim"]) + post["ext"]))

    print(f"Found {len(attachment_urls)} attachments")
    path = f"{SCRIPT_PATH}/attachments/{board}/{thread_id} - {thread_name}"

    os.makedirs(path, exist_ok=True)

    async with httpx.AsyncClient() as client:
        tasks = [download_attachment(client, path, attachment_url) for attachment_url in attachment_urls]
        await asyncio.gather(*tasks)

    print("\nDone")



if __name__ == "__main__":
   asyncio.run(main())   