from argparse import ArgumentParser
import asyncio

def setup_args():
    arg_parser = ArgumentParser(description="CLI Example")
    arg_parser.add_argument(
        "folder", metavar="folder_name", help="Photos Folder")
    arg_parser.add_argument(
        "album", metavar="album_name", help="Album name to be saved")

    return arg_parser.parse_args()


def main(args):
    pass


if __name__ == "__main__":
    args = setup_args()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(args))
