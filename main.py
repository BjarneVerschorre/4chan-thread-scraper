import os
import re
import asyncio
import threading
import httpx


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
    res = httpx.get(thread_info_url).json()

    thread_id = res["posts"][0]["no"]

    # Sanitize thread name for folder name
    thread_name = res["posts"][0]["sub"]
    thread_name = thread_name.replace("/", "-")
    thread_name = re.match(r"[a-zA-Z0-9 ]+", thread_name).group(0).strip()
    print(thread_name)
 

    attachment_urls = []
    for post in res["posts"]:
        if not "tim" in post:
            continue
        attachment_urls.append(attachment_url(board, str(post["tim"]) + post["ext"]))

    print(f"Found {len(attachment_urls)} attachments")
    path = f"attachments/{board}/{thread_id} - {thread_name}"

    os.makedirs(path, exist_ok=True)

    async with httpx.AsyncClient() as client:
        tasks = [download_attachment(client, path, attachment_url) for attachment_url in attachment_urls]
        await asyncio.gather(*tasks)

    print("\nDone")



if __name__ == "__main__":
   asyncio.run(main())   