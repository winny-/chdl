import asyncio
import aiohttp
from urllib.parse import urlparse
import re
from collections import namedtuple
from argparse import ArgumentParser
from os import path
import os
import sys
import humanize
from functools import partial


ThreadInfo = namedtuple('ThreadInfo', ['id', 'board'])


class Unbuffered(object):
    """Create a wrapped file-like object that is unbuffered."""
    def __init__(self, stream):
        self.stream = stream

    def write(self, data):
        self.stream.write(data)
        self.stream.flush()

    def __getattr__(self, attr):
        return getattr(self.stream, attr)


def get_thread_info(url):
    """Get the 4chan thread info from an URL."""
    parts = urlparse(url)
    if parts.hostname != 'boards.4chan.org':
        raise RuntimeError('Invalid url')
    m = re.match(r'^/(\w+)/thread/(\d+)', parts.path.lower())
    if m is None:
        raise RuntimeError('Invalid url')
    return ThreadInfo(id=m.group(2), board=m.group(1))


async def get_json(url):
    r = await aiohttp.get(url)
    return await r.json()


async def download_file(url, dest, progress=None):
    """Download a file

    url      -- the HTTP/HTTPS URL.
    dest     -- the path to save the data to.
    progress -- a callback to invoke once the file is downloaded
    """
    async with aiohttp.get(url) as r:
        with open(dest, 'wb') as f:
            while True:
                chunk = await r.content.read(1024)
                if not chunk:
                    break
                f.write(chunk)
    if progress is not None:
        progress()


def make_parser():
    """Make an ArgumentParser instance for chdl."""
    parser = ArgumentParser(description='Download 4chan images.')
    parser.add_argument('url')
    parser.add_argument(
        '--dest',
        '-d',
        help='The folder to download to',
        default='.',
    )
    parser.add_argument(
        '--no-create-thread-folder',
        '-n',
        help='Do not create a thread folder in --dest or cwd.',
        action='store_true',
    )
    return parser


async def download_images(thread_info, dest, posts):
    pass


def build_download_path(info, dest, no_create_thread_folder):
    """Build the download path for a given application state.

    info                    -- ThreadInfo namedtuple.
    dest                    -- The dest directory.
    no_create_thread_folder -- Should the dest dir have another folder in it?

    Returns a string of the path.
    """
    dest = path.expanduser(dest)
    if not no_create_thread_folder:
        dest = path.join(dest, '{id} ({board})'.format(
            id=info.id,
            board=info.board,
        ))
    return dest


def main():
    """Program entry point."""
    # Unbuffer stdout so progress is indicated responsively.
    sys.stdout = Unbuffered(sys.stdout)

    parser = make_parser()
    args = parser.parse_args()

    info = get_thread_info(args.url)
    dest = build_download_path(info,
                               args.dest,
                               args.no_create_thread_folder)

    loop = asyncio.get_event_loop()

    print('Getting thread information... ', end='')
    cor = get_json('https://a.4cdn.org/{0}/thread/{1}.json'.format(info.board,
                                                                   info.id))
    j = loop.run_until_complete(cor)
    print('Ok.')

    image_posts = [p for p in j['posts']
                   if 'filename' in p and 'filedeleted' not in p]

    if not image_posts:
        print('No images in thread. Exiting.')
        return

    size = sum(p['fsize'] for p in image_posts)

    print('{} images to download, {} total.'.format(
        len(image_posts),
        humanize.naturalsize(size, binary=True),
    ))

    os.makedirs(dest, mode=0o755, exist_ok=True)
    if not os.access(dest, os.W_OK):
        print('No write access to "{}". Exiting.'.format(dest))
        return

    print('Downloading to "{}"'.format(dest))

    L = []
    for p in image_posts:
        filename = '{}{}'.format(p['tim'], p['ext'])
        url = 'https://i.4cdn.org/{}/{}'.format(info.board, filename)
        L.append(download_file(
            url,
            path.join(dest, filename),
            progress=partial(print, '.', end=''),
        ))

    # FIXME: Use a queue instead of starting all downloads at once!
    r = asyncio.gather(*L)

    loop.run_until_complete(r)

    print()  # Print newline after the 'progress periods'.
    print('Finished downloading images.')
