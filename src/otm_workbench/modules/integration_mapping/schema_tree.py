import json
from pathlib import Path
import xml.etree.ElementTree as ET


def xml_node(element: ET.Element, parent_path: str = "") -> dict[str, object]:
    path = f"{parent_path}/{element.tag}" if parent_path else f"/{element.tag}"
    children = [xml_node(child, path) for child in list(element)]
    return {
        "name": element.tag,
        "path": path,
        "node_type": "object" if children else "value",
        "children": children,
    }


def parse_xml_schema_tree(content: str) -> dict[str, object]:
    root = ET.fromstring(content)
    return xml_node(root)


def scalar_type(value: object) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int | float):
        return "number"
    if value is None:
        return "null"
    return "string"


def json_node(name: str, value: object, path: str) -> dict[str, object]:
    if isinstance(value, dict):
        return {
            "name": name,
            "path": path,
            "node_type": "object",
            "children": [json_node(str(key), child, f"{path}.{key}") for key, child in value.items()],
        }
    if isinstance(value, list):
        sample = value[0] if value else {}
        children = []
        if isinstance(sample, dict):
            children = [json_node(str(key), child, f"{path}[].{key}") for key, child in sample.items()]
        elif value:
            children = [json_node("value", sample, f"{path}[]")]
        return {
            "name": name,
            "path": f"{path}[]",
            "node_type": "array",
            "children": children,
        }
    return {
        "name": name,
        "path": path,
        "node_type": scalar_type(value),
        "children": [],
    }


def parse_json_schema_tree(content: str) -> dict[str, object]:
    payload = json.loads(content)
    return json_node("$", payload, "$")


def parse_payload_artifact_schema_tree(file_path: str, payload_format: str) -> dict[str, object]:
    content = Path(file_path).read_text(encoding="utf-8")
    normalized_format = payload_format.strip().upper()
    if normalized_format == "XML":
        return parse_xml_schema_tree(content)
    if normalized_format == "JSON":
        return parse_json_schema_tree(content)
    raise ValueError("payload_format_unsupported")
