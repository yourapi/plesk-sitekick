#!/usr/bin/env python3 .domains-to-sitekick.py
# -*- coding: utf-8 -*-
# File: domains-to-sitekick.py
# The shebang does not work on CentOS plesk servers. Use the following command to run the script:
# python3 domains-to-sitekick.py
# or add it to a crontab to run regularly (for instance every day at 2am):
# 0 2 * * * python3 /home/src/plesk-sitekick/domains-to-sitekick.py
# assuming the file is located in /home/src/plesk-sitekick
"""
Create a token for a Sitekick server, if it does not exist. This file can be executed every day to make sure that new
Sitekick-servers are added and that deprecated servers will be cleaned up.

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
import random
import threading
import time
from importlib import import_module
from pathlib import Path
from urllib.request import urlopen, Request

from sitekick.config import QUEUE_PATH, PLESK_COMMUNICATION_TOKEN, SITEKICK_PUSH_URL
from sitekick.server_info import ip_address
from sitekick.utils import now


# Get a list of filenames for the providers and see which ones are appropriate:
def get_providers():
    """Return a list of providers for which the is_server_type() returns True-ish."""
    providers = []
    for filename in Path(__file__).parent.glob('providers/*.py'):
        if filename.stem == '__init__':
            continue
        module = __import__(f"providers.{filename.stem}", fromlist=['is_server_type'])
        if module.is_server_type():
            providers.append(module)
    return providers


def get_domains_info(domains=None, queue_path=QUEUE_PATH, cleanup=False):
    """Get domain info from the local Plesk server and store the data per domain in a file in `queue_path`.
    From there, the data is periodically pushed to the Sitekick-server."""
    # Get all domains from the local Plesk server:
    if domains is None:
        domains = get_domains()
    Path(queue_path).mkdir(parents=True, exist_ok=True)
    # Clear the queue location:
    if cleanup:
        for filename in Path(queue_path).glob('*'):
            filename.unlink()
    # Get detailed information per domain and store it in the file system.
    for i, domain in enumerate(domains):
        domain_info = None
        for attempt in range(10):
            try:
                domain_info = get_domain_info(domain)
                break
            except Exception as e:
                print(
                    f"{now()} Sitekick get_domain_info attempt {attempt + 1} of 10 for {domain} failed with exception: {e}")
                time.sleep((5 ** (attempt / 9)))
        if domain_info is None:
            print(f"{now()} Sitekick get_domain_info for {domain} failed 10 times, skipping this domain")
            continue
        with Path(queue_path, f"{i:08}-{domain}.json").open('w') as f:
            f.write(json.dumps(domain_info, indent=4))
        if i % 100 == 0:
            print(f"{i} {now()}: {domain} (Sitekick)", flush=True)
        else:
            print('.', end='', flush=True)
    print(f"\n{now()} Sitekick {len(domains)} domains info stored in {queue_path}")


def push_domains_info(queue_path=QUEUE_PATH, count=200, interval=100, interval_offset=None, attempts=10):
    """Every `interval` seconds, get the files from the queue_path and push them to the Sitekick server.
    The `interval_offset` is used to start pushing after a certain number of seconds, when not specified, use the local
    ip-address to generate a random offset. This way, the load is spread when a large number of servers (hundreds or
    even thousands) simultaneously push their data.
    Push at most `count` files.
    Continue until no more files are found."""
    if interval_offset is None:
        # Use the server's IP-address as seed te generate a random offset which is nonetheless repeatable:
        random.seed(ip_address)
        interval_offset = random.random() * interval
    total_count = 0
    send_files_previous = []
    while True:
        # Start with waiting to let files enter the directory:
        time_next = (time.time() // interval + 1) * interval + interval_offset
        time.sleep(
            max(time_next - time.time(), interval / 2))  # prevent edge cases, always sleep at least half the interval
        files_in_queue = list(Path(queue_path).glob('*'))
        files_in_queue.sort(key=lambda file: file.name)
        send_files = files_in_queue[:count]
        if not send_files or set(send_files) == set(send_files_previous):
            # No more files or no new files, stop pushing:
            break
        send_files_previous = send_files
        data = []
        for file in send_files:
            with file.open() as f:
                data.append(json.loads(f.read()))
        # Now push the data to the Sitekick server, with a maximum `attempts` number of attempts:
        for attempt in range(attempts):
            req = Request(SITEKICK_PUSH_URL,
                          method='POST', data=json.dumps(data).encode(),
                          headers={'Authorization': f'Bearer {PLESK_COMMUNICATION_TOKEN}',
                                   'Content-Type': 'application/json',
                                   'Accept': 'application/json'})
            try:
                response = urlopen(req)
                if 200 <= response.getcode() < 300:
                    # Remove the files from the queue:
                    for file in send_files:
                        file.unlink()
                    total_count += len(send_files)
                    print(
                        f"\n{now()} Sitekick pushed {total_count - len(send_files)}:{total_count} files to {SITEKICK_PUSH_URL}")
                    break
                print(
                    f"\n{now()} Sitekick push attempt {attempt + 1} of {attempts} to {SITEKICK_PUSH_URL} failed with code {response.getcode()}: {response.read()}")
            except Exception as e:
                print(
                    f"\n{now()} Sitekick push attempt {attempt + 1} of {attempts} to {SITEKICK_PUSH_URL} failed with exception: {e}")
            time.sleep((60 ** (attempt / ((
                                                  attempts - 1) or 1))))  # Exponential backoff, starting with 1 second, ending with 1 minute in the last attempt
    print(f"\n{now()} Sitekick pushed total {total_count} files to {SITEKICK_PUSH_URL}")


def get_valid_server_modules(root_module='providers'):
    """Inspect all server modules and see which ones are valid by calling is_server_type(). When the module is valid,
    it is returned."""
    valid_modules = []
    for filename in Path(__file__).parent.parent.glob(f'{root_module}/*.py'):
        if filename.stem == '__init__':
            continue
        try:
            module = import_module(f"{root_module}.{filename.stem}")
            # A valid to_sitekick module should have three functions: is_server_type, get_domains and get_domain_info:
            for function in ['is_server_type', 'get_domains', 'get_domain_info']:
                if not hasattr(module, function):
                    raise AttributeError(f"Module {root_module}.{filename.stem} has no function {function}")
            try:
                if module.is_server_type():
                    valid_modules.append(module)
            except Exception as e:
                print(f"{root_module}.{filename.stem}.is_server_type(): False ({e})")
        except Exception as e:
            print(f"Error importing module {root_module}.{filename.stem}: {e}")
    return valid_modules


def main():
    # Now let the two functions (get_domains_info and push_domains_info) run in parallel:
    threads = [
        threading.Thread(target=get_domains_info),
        threading.Thread(target=push_domains_info)
    ]
    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()
