import argparse
from importlib import import_module
from pathlib import Path
from sitekick.main import main

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
    main()

def execute(args):
    """Execute the specified command."""
    exec(f"{args.command}(*{args.args})")