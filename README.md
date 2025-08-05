A command-line tool for generating reports from DHIS2 Scheduled Sync Job logs.

Supported Job types:

- Data synchronization.
- Event Programs Data Sync.
- Tracker Programs Data Sync.
- Metadata synchronization.

The script can access logs stored either on the local filesystem or inside Docker containers.

Requirements: Python 3.8+

## Install

User installation (no root permissions required):

```shell
$ python3 -m venv .venv # Initialize a virtual environment using system-wide python3 installation
$ .venv/bin/pip install --upgrade pip # Make sure we are using the latest pip package manager version
$ .venv/bin/pip install hatch # Strictly only needed for development
$ .venv/bin/pip install -e . # install d2-sync-report from sources
$ .venv/bin/d2-sync-report # Check that it works
```

## Usage

```shell
$ d2-sync-report --help
usage: d2-sync-report [-h] [OPTIONS]

╭─ options ───────────────────────────────────────────────────────────────────╮
│ -h, --help         show this help message and exit                          │
│ --logs-folder-path [DOCKER_CONTAINER:]FOLDER_PATH                           │
│                    Folder containing file dhis.log (required)               │
│ --url URL          DHIS2 instance base URL (required)                       │
│ --auth AUTH        USER:PASS or PAT token (required)                        │
│ --docker-container NAME                                                     │
│                    Docker container running in the instance (default: None) │
│ --suggestions-path PATH                                                     │
│                    Path to custom suggestions JSON file (default: None)     │
│ --ignore-cache, --no-ignore-cache                                           │
│                    Ignore cached state (default: False)                     │
│ --notify-user-group NAME or CODE                                            │
│                    User group to send the report to (default: None)         │
╰─────────────────────────────────────────────────────────────────────────────╯

```

Examples:

Process local logs and show the report on the screen:

```shell
$ d2-sync-report \
    --logs-folder-path="/path/to/dhis2/config/logs"
```

Process logs stored in a Docker container (`CONTAINER_NAME:LOGS_FOLDER_PATH`) and display the report:

```shell
$ d2-sync-report \
    --logs-folder-path="dhis2web-test-two-test:/opt/dhis2/config/local/logs"
```

Process local logs and send the report to every user in the "System admin" user group in some DHIS2 instance:

```shell
$ d2-sync-report \
    --logs-folder-path="/path/to/dhis2/config/logs" \
    --url="http://localhost:8080" \
    --auth="d2pat_12345" \
    --notify-user-group="System admin"
```

## Development

```shell
$ .venv/bin/hatch run test
$ .venv/bin/hatch run lint
$ .venv/bin/hatch run cli
```

## Custom suggestions

File `suggestions.json` holds a centralized reference for mapping known DHIS2-related error messages to clear, actionable suggestions that explain how to resolve them. It is designed to help users quickly understand and fix issues that appear during metadata or data sync operations.

Each entry in the JSON file is an object within the `"mappings"` list and contains two main fields:

- **`error`**: A string pattern that represents a recognizable part of an error message. It can include placeholders (e.g., `{username}`, `{program_id}`) to denote variable parts of the message.
- **`suggestion`**: A human-readable explanation with step-by-step instructions. It may reference the same placeholders used in the `error` to dynamically insert the actual values found in the error message at runtime.

#### Example Entry

```json
{
  "error": "Detail: Key (username)=({username}) already exists",
  "suggestion": "User with username '{username}' already exists. Go to {base_url}/dhis-web-user/index.html#/users?query={username} and delete it"
}
```

This entry will match an error like:

```
Detail: Key (username)=(marta) already exists
```

And produce a suggestion like:

```
User with username 'marta' already exists. Go to https://your.dhis2.instance/dhis-web-user/index.html#/users?query=marta and delete it
```

#### Interpolations

Variables of type `{var}` can be used to to match values in the error section and referenced in the suggestions sections.

Base Placeholder Variables:

| Placeholder          | Description                            | Example Value                |
| -------------------- | -------------------------------------- | ---------------------------- |
| `{base_url}`         | Root URL of the DHIS2 instance         | `https://play.dhis2.org/dev` |
| `{resources_folder}` | Path to local scripts or SQL resources | `/config/logs`               |
| `{docker_container}` | Name of the DHIS2 Docker container     | `dhis2_server`               |

Metadata-Based Placeholders:

| Placeholder Pattern | Description                                                   | Example Value           |
| ------------------- | ------------------------------------------------------------- | ----------------------- |
| `{xxx_id}`          | Metadata UID (e.g. program, org unit, option set)             | `j8v1Km9YP3r`           |
| `{xxx_name}`        | Friendly name for the same object, auto-resolved if available | `Malaria Case Tracking` |

Event-Specific Placeholders:

| Placeholder             | Description                                         | Example Value |
| ----------------------- | --------------------------------------------------- | ------------- |
| `{event_id}`            | UID of the event                                    | `x9ab12kXY78` |
| `{event_program}`       | UID of the event’s program                          | `a1b2cc3d4e5` |
| `{event_orgUnit}`       | Org unit UID where the event was created            | `yUzt2qDp1Qh` |
| `{event_enrollment}`    | Enrollment UID that the event belongs to            | `enr12356abc` |
| `{event_trackedEntity}` | Tracked Entity Instance (TEI) UID tied to the event | `tei987dzyxw` |
