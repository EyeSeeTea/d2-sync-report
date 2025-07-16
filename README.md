# Setup

```shell
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the CLI (development)
python -m d2_sync_report.cli --input-file sample.txt --verbose

# OR, install as a CLI script and use it anywhere
pip install -e .
d2-sync-report --input-file sample.txt --verbose
```

A CLI tool to generate reports from DHIS2 scheduled sync jobs. Supports:

- 	Event Programs Data Sync
