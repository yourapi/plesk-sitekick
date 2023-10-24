#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create a token for a Sitekick server, if it does not exist. This file can be executed every day to make sure that new
Sitekick-servers are added and that depracated servers will be cleaned up.
"""
import datetime
import json
import subprocess
import socket
from pprint import pprint

## getting the hostname by socket.gethostname() method
hostname = socket.gethostname()
## getting the IP address using socket.gethostbyname() method
ip_address = socket.gethostbyname(hostname)

def get_token(filename='/etc/plesk/tokens.json'):
    """Get a token for local API access. If it was not generated, generate a new one and store it in a safe location."""
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
        with open(filename, 'w') as f:
            f.write(json.dumps(tokens))

pprint(get_token())