import datetime
import socket
from uuid import getnode


hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)
try:
    mac_address = ':'.join(("%012X" % getnode())[i:i + 2] for i in range(0, 12, 2))
except:
    mac_address = None


def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
