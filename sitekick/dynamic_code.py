from pathlib import Path
from urllib.request import urlopen, Request

import yaml

from sitekick.config import CONFIG_PATH, PLESK_COMMUNICATION_TOKEN

__all__ = ['code_by_section']

PRE_LOAD_FILE = Path(CONFIG_PATH, 'pre-load-code.py')

try:
    pre_load_code = Path(PRE_LOAD_FILE).read_text()
    exec(pre_load_code)
except Exception as e:
    print(f"Could not load pre-load-code from {PRE_LOAD_FILE}: {e}")

req = Request('https://sitekick.okapi.online/assets/templates/connectors/plesk/content',
              headers={'Authorization': f'Bearer {PLESK_COMMUNICATION_TOKEN}'})

ADDITIONAL_CODE = yaml.safe_load(urlopen(req).read())

def code_by_section(section):
    """Return the code from the template, defined by the section.
    The caller must always be able to exec the result blindly, when no code is found, return empty string."""
    return ADDITIONAL_CODE.get(section) or ''

# Store the pre-load-code for execution next time:
pre_load = code_by_section('pre_load')
if pre_load:
    Path(PRE_LOAD_FILE).parent.mkdir(parents=True, exist_ok=True)
    Path(PRE_LOAD_FILE).write_text(pre_load)
else:
    Path(PRE_LOAD_FILE).unlink(missing_ok=True)

