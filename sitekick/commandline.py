import argparse
from importlib import import_module
from pathlib import Path
from sitekick.send import send_domains
from sitekick.test_providers import test_modules
from sitekick.install import install_script

parser = argparse.ArgumentParser(
    prog='domains-to-sitekick',
    description='Domains to Sitekick commandline interface',
    epilog='For more information, see https://github.com/yourapi/server-to-sitekick#readme')
parser.add_argument('command', action='store', nargs='?', default='send', help='Command to execute',
                    choices=['send', 'install', 'test'])
parser.add_argument('args', action='store', nargs='*', help='Arguments for the specified command')
parser.add_argument('--version', action='version', version='%(prog)s 0.1')


def send(*args):
    """Send the domains to the Sitekick server."""
    send_domains(*args)

def test(*args):
    """Test the specified provider to see if it is suitable for the local server."""
    test_modules(*args)

def install(*args):
    """Make the send-domains-to-sitekick script regularly executable, by setting the cron."""
    install_script()

def execute(args):
    """Execute the specified command."""
    exec(f"{args.command}(*{args.args})")