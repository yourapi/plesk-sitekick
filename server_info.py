# getting the hostname by socket.gethostname() method
import socket
from uuid import getnode

__all__ = ['hostname', 'ip_address', 'mac_address']

hostname = socket.gethostname()
# getting the IP address using socket.gethostbyname() method
ip_address = socket.gethostbyname(hostname)
# getting the mac address
try:
    mac_address = ':'.join(("%012X" % getnode())[i:i + 2] for i in range(0, 12, 2))
except:
    mac_address = None

