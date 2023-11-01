import json
import subprocess
from pathlib import Path

from urllib.request import Request, urlopen

from sitekick.utils import now
from sitekick.server_info import ip_address, hostname, mac_address

__all__ = ['is_server_type', 'get_domains', 'get_domain_info']

tokens = dict()


def is_server_type():
    """Returns True-ish if the server on which the server is running, is of the specified type.
    Returns False-ish or raise an error if not the specified type, the error is caught and the result is False-ish.
    Any non-False suffices, but extra information (like the server type and version) can be returned.
    E.g. when on a plesk-server the code `providers.plesk.is_server_type() is called, it returns a string with
    the version info."""
    return get_info_api('server')


def get_token(filename=f'/etc/plesk/tokens.json'):
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
                               f"Admin access token for {hostname} at {now()}"],
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


def get_domains():
    """Get all domains from the local Plesk server."""
    return get_info_cli('domain', '--list')

def get_domain_info(domain):
    """Get detailed information about the specified domain from the local Plesk server.
    When additional or different info is needed, change this function."""
    domain_info_lines = get_info_cli('domain', '--info', domain)
    # Convert the text info to a valid JSON string:
    domain_info = convert_domain_text_to_json(domain_info_lines)
    domain_info['Server'] = {'Hostname': hostname, 'IP-address': ip_address, 'MAC-address': mac_address}
    domain_info['domain'] = domain
    return domain_info

