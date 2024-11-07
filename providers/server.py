"""Return some vitals of the server, in the same way as domains.
"""
import subprocess
import sys

from sitekick.utils import now, hostname, ip_address, mac_address

EXECUTE_PARALLEL = False
DOMAIN_COUNT_PER_POST = 100
DOMAIN_POST_INTERVAL = 1

def is_server_type():
    """Is it a Linux-server?"""
    return sys.platform == 'linux'


def get_domains():
    """This is not a domain module, but only the data about this server."""
    return [ip_address]


def get_domain_info(domain):
    """Get detailed information about the specified domain from the local hosting server.
    When additional or different info is needed, change this function."""
    proc = subprocess.run(["uptime"],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # Now the token is in the output of the command. Store it in a safe location:
    uptime = proc.stdout.decode().strip()

    return {'uptime': uptime, 'ip': ip_address, 'mac': mac_address, 'hostname': hostname, 'now': now()}
