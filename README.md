A CLI tool to generate reports from DHIS2 scheduled sync jobs. Supports:

- Event Programs Data Sync
- Tracker Programs Data Sync

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
usage: d2-sync-report [-h] [OPTIONS]

╭─ options ───────────────────────────────────────────────╮
│ -h, --help              show this help message and exit │
│ --url STR               (required)                      │
│ --auth STR              (required)                      │
│ --send-user-group STR   (required)                      │
│ --logs-folder-path STR  (required)                      │
│ --skip-message, --no-skip-message                       │
│                         (default: False)                │
│ --ignore-cache, --no-ignore-cache                       │
│                         (default: False)                │
╰─────────────────────────────────────────────────────────╯
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
