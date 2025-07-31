import re
import json
from typing import Any, TypedDict, Optional, List
from string import Formatter

from d2_sync_report.data.dhis2_api import DictResponse, D2Api
from d2_sync_report.domain.entities.instance import Instance


class ErrorMapping(TypedDict):
    error: str
    suggestion: str


class D2LogsSuggestions:
    instance: Instance
    api: D2Api
    error_mappings: List[ErrorMapping]

    def __init__(self, api: D2Api):
        self.api = api
        self.instance = api.instance
        self.error_mappings = self._get_error_mappings_from_file("suggestions.json")

    def get_suggestions_from_error(self, error: str) -> List[str]:
        extra_variables = dict(base_url=self.instance.url.rstrip("/"))
        suggestions: List[str] = []

        for mapping in self.error_mappings:
            variables = self._extract_variables_from_error_template(error, mapping)
            if variables:
                variables2 = self._get_object_mapping_program_variables(variables)
                variables2.update(extra_variables)
                suggestion = mapping["suggestion"].format(**variables2)
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
                # Replace friendly placeholder {var} with regex group (?P<var>.+?)
                escaped = escaped.replace(re.escape(f"{{{field_name}}}"), f"(?P<{field_name}>.+?)")
        return re.compile(escaped)

    def _extract_variables_from_error_template(
        self, error_message: str, mapping: ErrorMapping
    ) -> Optional[dict[str, str | Any]]:
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
            plural_name = camel_name + "s"
            endpoint = f"/api/{plural_name}"

            response = self.api.get(
                path=endpoint,
                response_model=DictResponse,
                params=[("fields", "id,name"), ("filter", f"id:eq:{object_id}")],
            ).root

            entities = response.get(plural_name, [])
            print(f"Retrieved {len(entities)} entities for {object_id} from {endpoint}")

            if entities and "name" in entities[0]:
                result[name_key] = entities[0]["name"]
            else:
                result[name_key] = object_id

        return result
