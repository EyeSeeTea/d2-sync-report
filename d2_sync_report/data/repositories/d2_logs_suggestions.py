import re
import json
from pathlib import Path
from typing import Any, Literal, TypedDict, Optional, List
from string import Formatter
from importlib.resources import files

import requests

from d2_sync_report.data.dhis2_api import DictResponse, D2Api
from d2_sync_report.domain.entities.instance import Instance


class ErrorMapping(TypedDict):
    error: str
    suggestion: str


class ExtraVariables(TypedDict):
    base_url: str
    docker_container: str
    resources_folder: str


class D2LogsSuggestions:
    instance: Instance
    api: D2Api
    error_mappings: List[ErrorMapping]
    # dict with keys base_url and docker_container
    extra_variables: ExtraVariables

    def __init__(self, api: D2Api, suggestions_path: str):
        self.api = api
        self.instance = api.instance
        self.error_mappings = self._get_error_mappings_from_file(suggestions_path)
        self.extra_variables = {
            "base_url": api.instance.url.rstrip("/"),
            "docker_container": api.instance.docker_container or "UNDEFINED",
            "resources_folder": target_dir.as_posix(),
        }

    def copy_resources(self):
        copy_resources()

    def get_suggestions_from_error(self, error: str) -> List[str]:
        suggestions: List[str] = []

        for mapping in self.error_mappings:
            if (variables := self._extract_variables_from_template(error, mapping)) is not None:
                object_variables = self._get_object_mapping_program_variables(variables)
                object_variables.update(self.extra_variables)
                suggestion = mapping["suggestion"].format(**object_variables)
                suggestions.append(suggestion)

        return suggestions

    ## Private methods

    def _get_error_mappings_from_file(self, file_path: str) -> List[ErrorMapping]:
        with open(file_path, "r") as file:
            data = json.load(file)

        return data.get("mappings", [])

    def _extract_variables(self, template: str) -> re.Pattern[str]:
        """
        Converts a template like 'foo={bar}' into a regex with named groups.
        """
        escaped = re.escape(template)
        for _literal_text, field_name, _format_spec, _conversion in Formatter().parse(template):
            if field_name:
                # Replace friendly placeholder {var} with regex group (?P<var>)
                escaped = escaped.replace(
                    re.escape(f"{{{field_name}}}"), f"(?P<{field_name}>[\\w.]+)"
                )
        return re.compile(escaped)

    def _extract_variables_from_template(
        self, error_message: str, mapping: ErrorMapping
    ) -> Optional[dict[str, Any]]:
        regex = self._extract_variables(mapping["error"])
        match = regex.search(error_message)
        return match.groupdict() if match else None

    def _get_object_mapping_program_variables(self, variables: dict[str, Any]) -> dict[str, Any]:
        result = variables.copy()

        for key, object_id in variables.items():
            if not key.endswith("_id") or not isinstance(object_id, str):
                continue

            name_key = key.replace("_id", "_name")
            if name_key in result:
                continue

            base_name = key[:-3]
            camel_name = "".join(
                word.capitalize() if i else word for i, word in enumerate(base_name.split("_"))
            )
            plural_name = (
                (camel_name + "s") if not camel_name.endswith("y") else (camel_name[:-1] + "ies")
            )

            if plural_name == "events":
                namespace = self._get_event_namespace(object_id)
                if namespace:
                    result.update(namespace)
            elif plural_name == "trackedEntities":
                namespace = self._get_tracked_entity_namespace(object_id)
                if namespace:
                    result.update(namespace)
            else:
                entity = self._get_metadata_entity(object_id, plural_name)
                result[name_key] = entity["name"] if entity and "name" in entity else None

        return result

    def _get_metadata_entity(
        self, object_id: str, plural_name: str
    ) -> Optional[dict[Literal["name"], str]]:
        try:
            response = self.api.get(
                path=f"/api/{plural_name}",
                response_model=DictResponse,
                params=[("fields", "id,name"), ("filter", f"id:eq:{object_id}")],
            ).root
        except requests.exceptions.HTTPError as e:
            print(f"Error fetching {plural_name} with ID {object_id}: {e}")
            return None

        entities = response.get(plural_name, [])
        return entities[0] if entities else None

    def _get_event_namespace(self, event_id: str):
        try:
            response = self.api.get(
                path=f"/api/events/{event_id}",
                response_model=DictResponse,
            ).root
        except requests.exceptions.HTTPError as e:
            print(f"Error fetching event {event_id}: {e}")
            return None

        namespace: dict[str, Optional[str]] = {
            "event_id": event_id,
            "event_enrollment": response.get("enrollment"),
            "event_orgUnit": response.get("orgUnit"),
            "event_program": response.get("program"),
            "event_trackedEntity": response.get("trackedEntityInstance"),
        }

        return namespace

    def _get_tracked_entity_namespace(self, tei_id: str):
        try:
            response = self.api.get(
                path=f"/api/tracker/trackedEntities/{tei_id}",
                params=[("fields", "*,enrollments")],
                response_model=DictResponse,
            ).root
        except requests.exceptions.HTTPError as e:
            print(f"Error fetching event {tei_id}: {e}")
            return None

        enrollments = response.get("enrollments", [])
        enrollment = enrollments[0] if enrollments else None

        namespace: dict[str, Optional[str]] = {
            "tracked_entity_id": tei_id,
            "tracked_entity_enrollment": enrollment.get("enrollment") if enrollment else None,
            "tracked_entity_orgUnit": response.get("orgUnit"),
            "tracked_entity_program": enrollment.get("program") if enrollment else None,
        }

        return namespace


target_dir = Path("/tmp/d2-sync-report-resources")


def copy_resources():
    """
    Some of the suggestions involve running SQL queries, so let's copy the
    resources folder from the package to a temporary directory that the user can access.
    """
    source_package = "d2_sync_report.data.repositories.resources"
    source_path = files(source_package)
    target_dir.mkdir(parents=True, exist_ok=True)
    print("Copying resources from", source_path, "to", target_dir)

    for resource in source_path.iterdir():
        if not resource.name.endswith(".sql"):
            continue
        target_file = target_dir / resource.name
        target_file.write_text(resource.read_text(encoding="utf-8"))
        print(f"Copied: {resource.name} -> {target_file}")
