from sitekick.server_info import ip_address, hostname, mac_address
from sitekick.utils import now

__all__ = ['is_server_type', 'get_domains', 'get_domain_info']


def is_server_type():
    """Returns True-ish if the server on which the server is running, is of the specified type.
    Any non-False suffices, but extra information (like the server type and version) can be returned.
    E.g. when on a plesk-server the code `providers.plesk.is_server_type() is called, it returns a string with
    the version info."""
    return hostname == 'XPS17'


def get_domains():
    """Get all domains from the local Plesk server."""
    return ['sitekick.online', 'sitekick.com', 'sitekick.eu']


def get_domain_info(domain):
    """Get detailed information about the specified domain from the local Plesk server.
    When additional or different info is needed, change this function."""
    return {'domain': domain, 'ip': ip_address, 'mac': mac_address, 'hostname': hostname, 'now': now()}
