from sitekick.utils import now, hostname, ip_address, mac_address

EXECUTE_PARALLEL = False    # whether to execute the get_domains_info() and push_domains_info() calls in parallel
DOMAIN_COUNT_PER_POST = 20  # number of detailed domain info packages to send per post
DOMAIN_POST_INTERVAL = 1    # seconds

def is_server_type():
    """Returns True-ish if the server on which the server is running, is of the specified type.
    Any non-False suffices, but extra information (like the server type and version) can be returned.
    E.g. when on a plesk-server the code `providers.plesk.is_server_type() is called, it returns a string with
    the version info."""
    return hostname == 'XPS17'


def get_domains():
    """Get all domains from the local Plesk server."""
    return ['a{:03d}.sitekick.online'.format(i) for i in range(100)]


def get_domain_info(domain):
    """Get detailed information about the specified domain from the local Plesk server.
    When additional or different info is needed, change this function."""
    import time
    time.sleep(0.1)
    return {'domain': domain, 'ip': ip_address, 'mac': mac_address, 'hostname': hostname, 'now': now()}
