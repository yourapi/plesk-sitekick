#!/usr/bin/env python3 .domains-to-sitekick.py
# -*- coding: utf-8 -*-
# File: domains-to-sitekick.py
# The shebang does not work on CentOS plesk servers. Use the following command to run the script:
# python3 domains-to-sitekick.py
# or add it to a crontab to run regularly (for instance every day at 2am):
# 0 2 * * * python3 /home/src/plesk-sitekick/domains-to-sitekick.py
# assuming the file is located in /home/src/plesk-sitekick
"""
This file kickstarts the download and execution of the code from the Sitekick server.

Copyright 2023 Sitekick

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import json
import os
import socket
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen, Request

# Include the code fr downloading IN this file, to have a single installable file (easy to install):
CODE_ENDPOINT = 'https://sitekick.okapi.online/assets/templates/text'
CODE_BRANCH = 'dev'  # The branch field which is used to get the code from the `text` endpoint
CODE_REPO = 'server-to-sitekick'
try:
    __file__
except NameError:
    __file__ = os.path.abspath('domains-to-sitekick.py')


def load_code(root_path=None):
    """Load the code from the sitekick server and store it in the code directory.
    The code is refreshed when the code is pushed to the Git-repo."""
    if not root_path:
        root_path = Path(
            __file__).parent.parent  # The root path of the server-to-sitekick code, this code is in level 1
    if socket.gethostname() == 'XPS17':
        root_path /= 'test/code'
    # First get the list of all *.py files from the path recursively:
    existing_files = set(Path(root_path).rglob('*.py'))
    req = Request(CODE_ENDPOINT + f"?client={CODE_REPO}&branch={CODE_BRANCH}")
    files = json.loads(urlopen(req).read())
    for file in files:
        try:
            filename = Path(root_path, file['path'], file['name'])
            if (filename.exists()
                    and filename.stat().st_mtime >= datetime.strptime(file['_timestamp_'],
                                                                      '%Y-%m-%dT%H:%M:%S.%f%z').timestamp()):
                continue
            content = urlopen(Request(file['content'])).read()
            filename.parent.mkdir(parents=True, exist_ok=True)
            filename.write_bytes(content)
            with suppress(KeyError):
                existing_files.remove(filename)
        except Exception as e:
            print(f"Download of {file['content']} failed with exception: {e}")
            continue
    # Now remove the files which are no longer in the code directory:
    # for filename in existing_files:
    #     with suppress(OSError):
    #         filename.unlink()


# First, get the code from the Sitekick server and refresh all code:
load_code(Path(__file__).parent)
current_path = str(Path(__file__).parent)
print(f"current path: {current_path}")

# Now, set the python path dynamically to enable loading of modules:
if os.getenv('PYTHONPATH'):
    python_path = os.environ['PYTHONPATH'].split(os.pathsep)
    if current_path not in python_path:
        os.environ['PYTHONPATH'] = os.pathsep.join([current_path] + python_path)
else:
    os.environ['PYTHONPATH'] = current_path

print(f"python path: {os.environ['PYTHONPATH']}")


# Now the code is bootstrapped, import the main module and run it:
from sitekick.main import main
main()
