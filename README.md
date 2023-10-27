# Plesk - Sitekick
Connect a Plesk server to the Sitekick domain analysis and monitoring services.

## Introduction
Sitekick is a domain analysis and monitoring service that provides a comprehensive overview of the health of your domain.
Sitekick is used by major hosters for a number of applications: analysis, marketing, retention, monitoring, and more.
A major source of data is the actual hosting data, as it is provisioned by the hoster. One of the largest hosting
platforms is Plesk. This module provides a simple way to connect a Plesk server to Sitekick in a secure way.

## Installation
The file is a Python (3.5+) compatible script. It can be run on any Plesk server that has Python installed. The script
can be executed by calling python3, followed by the script name. The script has no dependencies on external modules. 
1. Copy the file `send-data-to-sitekick.py` to a location of your choice, e.g. `/usr/local/bin/` or
`/usr/local/src/`.
2. To run the script, run: `python3 /usr/local/src/send-data-to-sitekick.py`

## Configuration
The script requires no configuration. It stores files temporarily in the `/tmp/plesk/to_sitekick/domains` directory.
This location can be adjusted by changing the `QUEUE_PATH` variable in the script.

## Architecture
