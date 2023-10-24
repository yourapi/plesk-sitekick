#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Path: send-data-to-sitekick.py
# The shebang does not work on CentOS plesk servers. Use the following command to run the script:
# python3 send-data-to-sitekick.py
"""
Create a token for a Sitekick server, if it does not exist. This file can be executed every day to make sure that new
Sitekick-servers are added and that depracated servers will be cleaned up.
"""
import datetime
import json
import subprocess
import socket
from urllib.request import Request, urlopen
from pathlib import Path
from pprint import pprint

## getting the hostname by socket.gethostname() method
hostname = socket.gethostname()
## getting the IP address using socket.gethostbyname() method
ip_address = socket.gethostbyname(hostname)
tokens = {}

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
            with open(filename) as f:
                tokens = json.loads(f.read())
        except:
            tokens = {}
        tokens[hostname] = token
        # Create paths if necessary:
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        with open(filename, 'w') as f:
            f.write(json.dumps(tokens))
        return token

def get_info(endpoint, **kwargs):
    """Get the specified information form the specified end point on the local Plesk server. For information on getting
    Plesk information: https://docs.plesk.com/en-US/obsidian/api-rpc/about-rest-api.79359/"""
    url = f"https://{hostname}:8443/api/v2/{endpoint}"
    req = Request(url, headers={'X-API-Key': get_token(), 'Content-Type': 'application/json', 'Accept': 'application/json'})
    response = urlopen(req)
    return json.loads(response.read())

pprint(get_info('server'))
pprint(get_info('server/ips'))



