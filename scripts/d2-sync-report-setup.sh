#!/bin/bash
set -e -u -o pipefail

# This script automates the setup of the d2-sync-report tool for a Debian/Ubuntu system.
#
# Tasks performed:
#  - Install the tool from sources
#  - Set up a Python virtual environment and installs dependencies
#  - Create/refresh an API token for DHIS2
#  - Configure a cron job to run the report daily at 07:30 as the dhis2 user

# Usage (as root):
#
#   # DHIS2_URL=http://localhost:8080 DHIS2_AUTH='USER:PASS' bash d2-sync-report-setup.sh

folder="d2-sync-report"

debug() {
	echo "DEBUG: $*" 1>&2
}

install_cron() {
    local token=$1
    local sources line
	debug "Installing cron job"

    sources=$(realpath "$folder")
	file="/etc/cron.d/d2-sync-report"
	# shellcheck disable=SC2016
	template='30 07  * * *  dhis2  chronic $sources/.venv/bin/d2-sync-report --logs-folder-path /path/to/dhis2/config/logs --auth "$token" --url "$DHIS2_URL" --notify-user-group "Some Group"'
    line=$(echo "$template" | sources=$sources token=$token envsubst)

    touch "$file"

	# Remove any existing lines containing d2-sync-report
	sed -i '/d2-sync-report/d' "$file"

	# Append if missing
	if ! grep -qF "$line" "$file"; then
		echo "$line" | tee -a "$file"
	fi
}

apt_install() {
	apt-get update
	DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "$@"
}

install_from_sources() {
	debug "Installing d2-sync-report from sources"
	apt_install jq pip git curl gettext-base moreutils python3-venv

    rm -rf "$folder"
    git clone https://github.com/EyeSeeTea/d2-sync-report

	(
		cd $folder
		python3 -m venv .venv

		.venv/bin/pip install --upgrade pip
		.venv/bin/pip install hatch
		.venv/bin/pip install -e .
		.venv/bin/d2-sync-report --help # just to make sure it works
	)
}

curl_d2() {
	# shellcheck disable=SC2016
	curl -u "$DHIS2_AUTH" -sS "$@"
}

create_api_token() {
	local id="dHUFf32d6JO"

	debug "Deleting existing token with id $id, if any"
	curl_d2 -X DELETE "$DHIS2_URL/api/apiToken/$id" -o /dev/null || true

	debug "Creating API token"
	jq -n --arg id "$id" '{
		id: $id,
        expire: 2524608000000,
        attributes: [{ type: "MethodAllowedList", allowedMethods: ["GET","POST"]}]
	}' |
		curl_d2 -H "Content-Type: application/json" -X POST "$DHIS2_URL/api/apiToken" -d@- |
		jq -r '.response.key // error("missing response key")'
}

setup() {
	local token sources

	install_from_sources
	token=$(create_api_token)
	install_cron "$token"
}

main() {
	setup
	echo "Done"
}

main "$@"
