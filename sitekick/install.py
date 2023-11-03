import os
import random
import subprocess
from importlib import import_module
from pathlib import Path
from pprint import pprint

from sitekick.server_info import hostname, ip_address


def install_script():
    """Make the script run daily by setting the cron."""
    # Get the path to the script:
    script_path = Path(__file__).parent / 'domains-to-sitekick.py'
    # Get the path to the cron file:
    cron_path = Path('/etc/cron.d/sitekick')
    # Write the cron file. Set the time between 3 and 4 AM, by selecting a random minute, based on the hostname:
    random.seed(hostname + ip_address + 'cron')
    minute = random.randint(0, 59)
    text = "# Run the domains-to-sitekick script daily at a random minute between 3 and 4 AM.\n" \
           f"{minute} 3 * * * root python3 {script_path}"
    if os.geteuid() == 0:
        # Current user has write rights on the cron file, write the cron file:
        cron_path.open('w').write(text)
    else:
        op = '>'
        for line in text.split('\n'):
            proc = subprocess.run(['sudo', 'echo', f'"{line}"', op, str(cron_path)], shell=True, timeout=10,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            op = '>>'
    print(f"Written cron file {cron_path}")
