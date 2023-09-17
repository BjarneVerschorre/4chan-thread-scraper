import os
import re
import asyncio
import threading
import httpx

SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))


def get_thread_info(url:str):
    """ Returns the board and thread info url from a 4chan thread url """
    a = re.match(r"https://boards.4chan.org/(\w+)/thread/(\d+)", url)
    
    board = a.group(1)
    thread_id = a.group(2)
    thread_info_url = f"https://a.4cdn.org/{board}/thread/{thread_id}.json"

    return board, thread_info_url

def attachment_url(board:str, filename:str):
    """ Returns the url of an attachment from a board and filename """
    return f"https://i.4cdn.org/{board}/{filename}"

def save_attachment(attachment_data: bytes, path:str, file_name: str):
    with open(f"{path}/{file_name}", "wb") as f:
        f.write(attachment_data)

    print(f"\rDownloaded \"{file_name}\"", end="")

async def download_attachment(client: httpx.AsyncClient, path:str, attachment_url:str):
    res = await client.get(attachment_url)

    if res.status_code != 200:
        print(f"Failed to download \"{attachment_url}\"")
        return
    
    file_name = attachment_url.split("/")[-1]
    threading.Thread(target=save_attachment, args=(res.content, path, file_name)).start()


async def main():
    thread_url = input("4chan thread url: ")

    board, thread_info_url = get_thread_info(thread_url)
    thread_data:dict = httpx.get(thread_info_url).json()

    initial_post:dict = thread_data["posts"][0]
    thread_id:int = initial_post["no"]

    # Sanitize thread name for folder name
    thread_name:str = initial_post.get("sub", initial_post.get("com", "Unnamed thread"))
    thread_name = thread_name.replace("/", "-")
    thread_name = re.match(r"[a-zA-Z0-9 -]+", thread_name).group(0).strip()
 
    thread_posts:list[dict] = thread_data.get("posts", [])

    attachment_urls = []
    for post in thread_posts:
        if not "tim" in post:
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