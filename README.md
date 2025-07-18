A CLI tool to generate reports from DHIS2 scheduled sync job logs. Currently, it supports jobs of type:

-   Event Programs Data Sync
-   Tracker Programs Data Sync

Requirements: Python 3.8+

## Install

```shell
$ sudo apt install pipx
$ pipx install hatch
$ pipx install -e .
$ $HOME/.local/bin/d2-sync-report # add folder to the PATH
```

## Usage

```shell
$ d2-sync-report --help
usage: cli.py [-h] [OPTIONS]

╭─ options ────────────────────────────────────────────────╮
│ -h, --help         show this help message and exit       │
│ --url URL          DHIS2 instance base URL (required)    │
│ --auth AUTH        Basic auth (user:pass) (required)     │
│ --send-user-group GROUP_ID                               │
│                    User group UID (required)             │
│ --logs-folder-path PATH                                  │
│                    Folder containing dhis.log (required) │
│ --skip-message, --no-skip-message                        │
│                    Skip sending message (default: False) │
│ --ignore-cache, --no-ignore-cache                        │
│                    Ignore cached state (default: False)  │
╰──────────────────────────────────────────────────────────╯
```

Example:

```shell
$ d2-sync-report \
    --url="http://localhost:8080" \
    --auth="USER:PASS" \
    --send-user-group="System admin" \
    --logs-folder-path="/path/to/dhis2/config/logs"
```

## Development

```shell
$ hatch run cli
$ hatch run test
```
