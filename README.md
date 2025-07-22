A command-line tool for generating reports from DHIS2 scheduled sync job logs.

Supported job types:

- Data synchronization
- Event Programs Data Sync
- Tracker Programs Data Sync
- Metadata synchronization

The script can access logs stored either on the local filesystem or inside Docker containers.

Requirements: Python 3.8+

## Install

User installation (no root permissions required):

```shell
$ python3 -m venv .venv
$ .venv/bin/pip install --upgrade pip
$ .venv/bin/pip install hatch
$ .venv/bin/pip install -e .
$ .venv/bin/d2-sync-report
```

## Usage

```shell
$ d2-sync-report --help
usage: d2-sync-report [-h] [OPTIONS]

╭─ options ───────────────────────────────────────────────────────╮
│ -h, --help         show this help message and exit              │
│ --logs-folder-path [DOCKER_CONTAINER:]FOLDER_PATH               │
│                    Folder containing dhis.log (required)        │
│ --ignore-cache, --no-ignore-cache                               │
│                    Ignore cached state (default: False)         │
│ --url URL          DHIS2 instance base URL (default: None)      │
│ --auth AUTH        USER:PASS or PAT token (default: None)       │
│ --notify-user-group NAME or CODE                                │
│                    User group to send report to (default: None) │
╰─────────────────────────────────────────────────────────────────╯
```

Examples:

Process local logs and show the report on the screen:

```shell
$ d2-sync-report \
    --logs-folder-path="/path/to/dhis2/config/logs"
```

Process logs stored in a Docker container (use format `CONTAINER_NAME:LOGS_FOLDER_PATH`) and display the report on the screen:

```shell
$ d2-sync-report \
    --logs-folder-path="dhis2web-test-two-test:/opt/dhis2/config/local/logs"
```

Process local logs and send the report to every user in the "System admin" user group for the specified DHIS2 instance:

```shell
$ d2-sync-report \
    --logs-folder-path="/path/to/dhis2/config/logs" \
    --url="http://localhost:8080" \
    --auth="d2pat_12345" \
    --notify-user-group="System admin"
```

## Development

```shell
$ .venv/bin/hatch run cli
$ .venv/bin/hatch run test
```
