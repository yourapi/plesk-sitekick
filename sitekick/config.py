CONFIG_PATH = '/etc/server-to-sitekick'
# This token ONLY has access to two end points: /assets/templates/connectors/*plesk*/content and
# /client/administration/queues/*plesk*
PLESK_COMMUNICATION_TOKEN = 'Mq63bc7gj2U7ubF2kohvol0F'
QUEUE_PATH = '/tmp/plesk/sitekick/domains'
SITEKICK_PUSH_URL = 'https://sitekick.okapi.online/client/administration/queues/plesk-test'
CODE_ENDPOINT = 'https://sitekick.okapi.online/assets/templates/text'
CODE_BRANCH = 'dev'  # The branch field which is used to get the code from the `text` endpoint