"""Download all code from the sitekick server and store it in the code directory."""
import json
import os
from contextlib import suppress
from pathlib import Path
from urllib.request import urlopen, Request

from sitekick.config import CODE_ENDPOINT, CODE_BRANCH

__all__ = ['load_code']

from sitekick.server_info import hostname


def load_code(root_path=None):
    """Load the code from the sitekick server and store it in the code directory.
    The code is refreshed when the code is pushed to the Git-repo."""
    if not root_path:
        root_path = Path(__file__).parent.parent  # The root path of the server-to-sitekick code, this code is in level 1
    client = root_path.name  # The `client` field is (ab)used to specify the repo-name
    if hostname == 'XPS17':
        root_path /= 'test/code'
    # First get the list of all *.py files from the path recursively:
    existing_files = set(Path(root_path).rglob('*.py'))
    req = Request(CODE_ENDPOINT + f"?client={client}&branch={CODE_BRANCH}")
    files = json.loads(urlopen(req).read())
    for file in files:
        try:
            content = urlopen(Request(file['content'])).read()
            filename = Path(root_path, file['path'], file['name'])
            filename.parent.mkdir(parents=True, exist_ok=True)
            filename.write_bytes(content)
            with suppress(KeyError):
                existing_files.remove(filename)
        except Exception as e:
            print(f"Download of {file['content']} failed with exception: {e}")
            continue
    # Now remove the files which are no longer in the code directory:
    for filename in existing_files:
        with suppress(OSError):
            filename.unlink()

if __name__ == '__main__':
    load_code()