import re
from typing import Any, TypedDict, Optional, List
from string import Formatter

from d2_sync_report.data import dhis2_api
from d2_sync_report.domain.entities.instance import Instance


class ErrorMapping(TypedDict):
    error: str
    suggestion: str


def get_error_mappings_from_file(file_path: str) -> List[ErrorMapping]:
    import json

    with open(file_path, "r") as file:
        data = json.load(file)

    return data.get("mappings", [])


def extract_variables(template: str) -> re.Pattern[str]:
    """
    Converts a template like 'foo={bar}' into a regex with named groups.
    """
    escaped = re.escape(template)
    for _literal_text, field_name, *_ in Formatter().parse(template):
        if field_name:
            # Replace simple placeholder ({var}) with regex group (?P<var>.+?)
            escaped = escaped.replace(re.escape(f"{{{field_name}}}"), f"(?P<{field_name}>.+?)")
    return re.compile(escaped)


def extract_variables_from_error_template(
    error_message: str, mapping: ErrorMapping
) -> Optional[dict[str, str | Any]]:
    regex = extract_variables(mapping["error"])
    match = regex.search(error_message)
    if not match:
        return None
    return match.groupdict()


error_mappings = get_error_mappings_from_file("suggestions.json")


def get_suggestions_from_error(instance: Instance, error: str) -> List[str]:
    extra_variables = dict(base_url=instance.url.rstrip("/"))
    suggestions: List[str] = []

    for mapping in error_mappings:
        variables = extract_variables_from_error_template(error, mapping)
        if variables:
            variables2 = get_object_mapping_program_variables(instance, variables)
            variables2.update(extra_variables)
            suggestion = mapping["suggestion"].format(**variables2)
            suggestions.append(suggestion)

    return suggestions


def get_object_mapping_program_variables(
    instance: Instance, variables: dict[str, Any]
) -> dict[str, Any]:
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

        response: Any = dhis2_api.request(
            instance,
            method="GET",
            path=endpoint,
            response_model=dhis2_api.AnyResponse,
            params=[("fields", "id,name"), ("filter", f"id:eq:{object_id}")],
        )

        entities = response.get(plural_name, [])
        print(f"Retrieved {len(entities)} entities for {object_id} from {endpoint}")

        if entities and "name" in entities[0]:
            result[name_key] = entities[0]["name"]
        else:
            result[name_key] = object_id

    return result
