#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Path: send-data-to-sitekick.py
# The shebang does not work on CentOS plesk servers. Use the following command to run the script:
# python3 send-data-to-sitekick.py
"""
Create a token for a Sitekick server, if it does not exist. This file can be executed every day to make sure that new
Sitekick-servers are added and that deprecated servers will be cleaned up.
"""
import datetime
import json
import random
import socket
import subprocess
import threading
import time
import yaml
from pathlib import Path
from urllib.request import Request, urlopen
from uuid import getnode

PLESK_COMMUNICATION_TOKEN = 'Mq63bc7gj2U7ubF2kohvol0F'
req = Request('https://sitekick.okapi.online/assets/templates/connectors/plesk/content',
              headers={'Authorization': f'Bearer {PLESK_COMMUNICATION_TOKEN}'})
ADDITIONAL_CODE = yaml.safe_load(urlopen(req).read())

def code_by_section(section):
    """Return the code from the template, defined by the section.
    The caller must always be able to exec the result blindly, when no code is found, return empty string."""
    return ADDITIONAL_CODE.get(section) or ''

# getting the hostname by socket.gethostname() method
hostname = socket.gethostname()
# getting the IP address using socket.gethostbyname() method
ip_address = socket.gethostbyname(hostname)
# getting the mac address
try:
    mac_address = ':'.join(("%012X" % getnode())[i:i+2] for i in range(0, 12, 2))
except:
    mac_address = None

tokens = {}

QUEUE_PATH = '/var/plesk/cache/to_sitekick/domains'
SITEKICK_PUSH_URL = 'https://sitekick.okapi.online/client/administration/queues/plesk'

def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Additional or changed init-data can be added here:
exec(code_by_section('init'))

def get_token(filename='/etc/plesk/tokens.json'):
    """Get a token for local API access. If it was not generated, generate a new one and store it in a safe location."""
    global tokens
    if hostname in tokens:
        return tokens[hostname]
    try:
        with open(filename) as f:
            tokens = json.loads(f.read())
            return tokens[hostname]
    except:
        # No token stored for this server. Generate a new one and store it in a safe location.
        # Get a token with the plesk bin secret_key tool and store it. First get the local IP-address:
        proc = subprocess.run(["plesk", "bin", "secret_key", "-c", "-ip-address", ip_address, "-description",
                               f'"Admin access token for {hostname} on {datetime.date.today()}"'],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # Now the token is in the output of the command. Store it in a safe location:
        token = proc.stdout.decode().strip()
        try:
            with Path(filename).open() as f:
                tokens = json.loads(f.read())
        except:
            tokens = {}
        tokens[hostname] = token
        # Create paths if necessary:
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        with open(filename, 'w') as f:
            f.write(json.dumps(tokens))
        return token

def get_info_api(endpoint, method=None, data=None):
    """Get the specified information form the specified end point on the local Plesk server. For information on getting
    Plesk information: https://docs.plesk.com/en-US/obsidian/api-rpc/about-rest-api.79359/"""
    url = f"https://{hostname}:8443/api/v2/{endpoint}"
    req = Request(url,
                  data=data,
                  headers={
                      'X-API-Key': get_token(),
                      'Content-Type': 'application/json',
                      'Accept': 'application/json'},
                  method=method)
    response = urlopen(req)
    result = response.read()
    try:
        return json.loads(result)
    except:
        try:
            return result.decode()
        except:
            return result

cli_commands = set(get_info_api('cli/commands'))

def get_info_cli(command, *args):
    """Get the specified information form the specified end point on the local Plesk server using the CLI. The CLI is
     executed using the API"""
    result = get_info_api(f"cli/{command}/call", method='POST', data=json.dumps({'params': args}).encode())
    # The result is a number of lines with the result. If it contains a tab character, it is a table. Convert to JSON:
    lines = result.get('stdout', '').split('\n')
    if lines and '\t' in lines[0]:
        return [dict([line.split('\t', 1)]) for line in lines]
    return lines

def convert_domain_text_to_json(domain_info_lines: list) -> dict:
    """Get the domain info as a number of lines and convert it to Python dict structure. An example of the text output:
    General
=============================
Domain name:                            sitekick.eu
Owner's contact name:                   Administrator (admin)
Domain status:                          OK
Creation date:                          Oct 20, 2023
Total size of backup files in local storage:0 B
Traffic:                                0 B/Month

Hosting
=============================
Hosting type:                           Physical hosting
IP Address:                             145.131.8.226
FTP Login:                              sitekick.eu_34gqrbu1k9m
FTP Password:                           ************
SSH access to the server shell under the subscription's system user:/bin/false
Hard disk quota:                        Unlimited (not supported)
Disk space used by httpdocs:            96.0 KB
Disk space used by Log files and statistical reports:28.0 KB
SSL/TLS support:                        On
Permanent SEO-safe 301 redirect from HTTP to HTTPS:On
PHP support:                            Yes
Python support:                         No
Web statistics:                         AWStats
Anonymous FTP:                          No
Disk space used by Anonymous FTP:       0 B

Web Users
=============================
Total :                                 0
PHP support:                            0
Python support:                         0
Total size:                             0 B

Mail Accounts
=============================
Mail service:                           On
Total :                                 3
Total size:                             0 B
Mail autodiscover:                      On

Must be converted to JSON:
{
    "General": {
        "Domain name": "sitekick.eu",
        "Owner\"s contact name": "Administrator (admin)",
        "Domain status": "OK",
        "Creation date": "Oct 20, 2023",
        "Total size of backup files in local storage": "0 B",
        "Traffic": "0 B/Month"
    },
    "Hosting": {
        "Hosting type": "Physical hosting",
        "IP Address": "..."
    }
}"""
    result = {}
    current_section = None
    prev_line = None
    for line in domain_info_lines:
        if line.startswith('==='):
            current_section = prev_line
            result[current_section] = {}
        elif current_section and line and ':' in line:
            key, value = line.split(':', 1)
            result[current_section][key.strip()] = value.strip()
        prev_line = line
    return result


def get_domain_info(domain):
    """Get detailed information about the specified domain from the local Plesk server.
    When additional or different info is needed, change this function."""
    domain_info_lines = get_info_cli('domain', '--info', domain)
    # Convert the text info to a valid JSON string:
    domain_info = convert_domain_text_to_json(domain_info_lines)
    domain_info['Server'] = {'Hostname': hostname, 'IP-address': ip_address, 'MAC-address': mac_address}
    domain_info['domain'] = domain
    return domain_info

# Optional change standard functions to get additional or different info:
exec(code_by_section('get_domain_info'))


def get_domains_info(domains=None, queue_path=QUEUE_PATH, cleanup=False):
    """Get domain info from the local Plesk server and store the data per domain in a file in `queue_path`.
    From there, the data is periodically pushed to the Sitekick-server."""
    # Get all domains from the local Plesk server:
    if domains is None:
        domains = get_info_cli('domain', '--list')
    Path(queue_path).mkdir(parents=True, exist_ok=True)
    # Clear the queue location:
    if cleanup:
        for filename in Path(queue_path).glob('*'):
            filename.unlink()
    # Get detailed information per domain and store it in the file system.
    for i, domain in enumerate(domains):
        domain_info = get_domain_info(domain)
        with Path(queue_path, f"{i:08}-{domain}.json").open('w') as f:
            f.write(json.dumps(domain_info, indent=4))
        if i % 100 == 0:
            print(f"{i} {now()}: {domain}", flush=True)
        else:
            print('.', end='', flush=True)


def push_domains_info(queue_path=QUEUE_PATH, count=2, interval=30, interval_offset=None, attempts=10):
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
    while True:
        # Start with waiting to let files enter the directory:
        time_next = (time.time() // interval + 1) * interval + interval_offset
        time.sleep(max(time_next - time.time(), interval / 2))  # prevent edge cases, always sleep at least half the interval
        files_in_queue = list(Path(queue_path).glob('*'))
        files_in_queue.sort(key=lambda file: file.name)
        send_files = files_in_queue[:count]
        if not files_in_queue:
            break
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
            response = urlopen(req)
            if 200 <= response.getcode() < 300:
                # Remove the files from the queue:
                for file in send_files:
                    file.unlink()
                total_count += len(send_files)
                print(f"\n{now()} Pushed {len(send_files)} of {total_count} files to {SITEKICK_PUSH_URL}")
                break
            time.sleep((60 ** (attempt/((attempts - 1) or 1))))  # Exponential backoff, starting with 1 second, ending with 1 minute in the last attempt
    print(f"\n{now()} Pushed total {total_count} files to {SITEKICK_PUSH_URL}")

# Optional change standard functions to get additional or different info:
exec(code_by_section('push_pull'))

# Now let the two functions (get_domains_info and push_domains_info) run in parallel:
threads = [
    threading.Thread(target=get_domains_info),
    threading.Thread(target=push_domains_info)
]
for thread in threads:
    thread.start()

for thread in threads:
    thread.join()

# Any cleanup, additional or changed actions can be added here:
exec(code_by_section('finalize'))
