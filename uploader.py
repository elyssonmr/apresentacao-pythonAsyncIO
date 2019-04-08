from argparse import ArgumentParser
import asyncio
from concurrent.futures import ThreadPoolExecutor
import imghdr
import os

from aiohttp import ClientSession, ClientTimeout, TCPConnector
from google_auth_oauthlib.flow import InstalledAppFlow


def setup_args():
    arg_parser = ArgumentParser(description="Google Photos Uploader")
    arg_parser.add_argument(
        "folder", help="Folder where phots should be searched"
    )
    arg_parser.add_argument(
        "album", help="Album name", default="New Album")

    return arg_parser.parse_args()


def get_api_token():
    flow = InstalledAppFlow.from_client_secrets_file(
        'client_id.json',
        scopes=['https://www.googleapis.com/auth/photoslibrary']
    )

    credentials = flow.run_console()
    token = credentials.token

    return token


def printProgressBar(iteration, total, prefix='', suffix='', decimals=1,
                     length=100, fill='█'):
    """
    Source:
    https://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console
    """
    percent = ("{0:." + str(decimals) + "f}").format(
        100 * (iteration / float(total))
    )
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end='\r')
    # Print New Line on Complete
    if iteration == total:
        print()


class Uploader:
    def __init__(self, args, token, loop, executor):
        self.folder = args.folder
        self.album = args.album
        self.loop = loop
        self.token = token
        self.executor = executor
        self.status = {
            "total": 0,
            "uploaded": 0
        }
        self.session = ClientSession(
            connector=TCPConnector(limit=2),
            timeout=ClientTimeout(total=0),
            headers={"Authorization": f"Bearer {self.token}"}
        )

    async def do_post(self, url, body="", headers={}):
        args = {"headers": headers}
        if isinstance(body, dict):
            args["json"] = body
        else:
            args["data"] = body

        return await self.session.post(url, **args)

    def get_folder_photos(self):
        files = os.listdir(self.folder)
        photos = []
        for image in files:
            img_path = os.path.join(self.folder, image)
            try:
                if imghdr.what(img_path):
                    photos.append(img_path)
            except Exception:
                pass

        return photos

    async def create_album(self):
        url = "https://photoslibrary.googleapis.com/v1/albums"
        remote_folder = {
            "album": {
                "title": self.album,
                "isWriteable": True
            }
        }

        resp = await self.do_post(
            url, remote_folder,
            {"ContentType": "application/json"}
        )
        created_album = await resp.json()
        resp.close()

        return created_album

    def read_file(self, file_path):
        with open(file_path, "br") as img_file:
            return img_file.read()

    def print_status(self):
        printProgressBar(
            self.status["uploaded"], self.status['total'],
            prefix='Uploading photos:', suffix='Complete', length=50
        )

    async def upload_to_google(self, photo):
        url = "https://photoslibrary.googleapis.com/v1/uploads"

        headers = {
            "Content-type": "application/octet-stream",
            "X-Goog-Upload-File-Name": photo.split("/")[-1],
            "X-Goog-Upload-Protocol": "raw"
        }
        data = await loop.run_in_executor(self.executor, self.read_file, photo)
        resp = await self.do_post(url, data, headers)
        content = await resp.text()
        resp.close()
        if resp.status != 200:
            print(f"Failed to upload {photo} to Google Photos")
            raise Exception(content)

        self.status["uploaded"] += 1
        self.print_status()
        return content

    async def add_to_album(self, tokens, album):
        url = "https://photoslibrary.googleapis.com/v1/mediaItems:batchCreate"
        upload_body = {
            "albumId": album["id"]
        }
        media_items = []
        for photo_token in tokens:
            photo = {
                "description": "AsyncIO CLI uploader",
                "simpleMediaItem": {
                    "uploadToken": photo_token
                }
            }
            media_items.append(photo)
        upload_body["newMediaItems"] = media_items
        resp = await self.do_post(
            url, upload_body, {"ContentType": "application/json"}
        )
        resp.close()

    async def assign_album(self, tokens, album):
        initial_window = 0
        final_window = 50
        total = len(tokens)
        while initial_window < total:
            album_tokens = tokens[initial_window:final_window]
            await self.add_to_album(album_tokens, album)
            initial_window += 50
            final_window += 50

    async def run(self):
        print("Getting folder photos")
        photos = self.get_folder_photos()
        if not photos:
            print("There is no image to be uploaded")
            await self.session.close()
            return

        print("Creating album")
        album = await self.create_album()
        uploads = []
        self.status["total"] = len(photos)
        for photo in photos:
            uploads.append(self.upload_to_google(photo))

        self.print_status()
        photo_tokens = await asyncio.gather(*uploads)
        print("Photos Uploaded")
        print(f"Adding them to {self.album}")
        await self.assign_album(photo_tokens, album)
        print(f"Uploaded {len(photos)} to {self.album}")
        await self.session.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    executor = ThreadPoolExecutor(5)
    args = setup_args()
    google_token = get_api_token()
    photo_uploader = Uploader(args, google_token, loop, executor)
    loop.run_until_complete(photo_uploader.run())
