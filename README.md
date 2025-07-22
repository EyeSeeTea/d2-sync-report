A command-line tool for generating reports from DHIS2 scheduled sync job logs.

Supported job types:

- Data synchronization
- Event Programs Data Sync
- Tracker Programs Data Sync
- Metadata synchronization

Requirements: Python 3.8+

## Install

Using pipx:

```shell
$ sudo apt install pipx # For Debian/Ubuntu,
$ pipx install hatch
$ pipx install -e .
$ pipx ensurepath  # Adds pipx's bin directory to PATH. Restart shell for changes to take effect.
```

## Usage

```shell
$ d2-sync-report --help
usage: d2-sync-report [-h] [OPTIONS]

╭─ options ───────────────────────────────────────────────────────╮
│ -h, --help         show this help message and exit              │
│ --logs-folder-path FOLDER_PATH                                  │
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

Process logs and show report in screen:

```shell
$ d2-sync-report \
    --logs-folder-path="/path/to/dhis2/config/logs"
```

Process logs and send the report to users in the "System admin" group on the specified DHIS2 instance:

```shell
$ d2-sync-report \
    --logs-folder-path="/path/to/dhis2/config/logs" \
    --url="http://localhost:8080" \
    --auth="admin:district" \
    --notify-user-group="System admin"
```

## Development

```shell
$ hatch run cli
$ hatch run test
```
