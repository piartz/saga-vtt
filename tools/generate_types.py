#!/usr/bin/env python3
"""
Code generator: Reads protocol.json schema and generates Python TypedDicts

Usage: python tools/generate_types.py
"""

import json
from pathlib import Path
from typing import Any, Dict, List

SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "protocol.json"
OUTPUT_PATH = Path(__file__).parent.parent / "services" / "api" / "app" / "protocol_generated.py"


def json_schema_type_to_python(schema: Dict[str, Any], definitions: Dict[str, Any]) -> str:
    """Convert JSON Schema type to Python type annotation"""

    if "$ref" in schema:
        ref_name = schema["$ref"].split("/")[-1]
        return ref_name

    if "oneOf" in schema:
        types = [json_schema_type_to_python(s, definitions) for s in schema["oneOf"]]
        return " | ".join(types)

    schema_type = schema.get("type")

    if schema_type == "string":
        if "enum" in schema:
            values = ", ".join(f'"{v}"' for v in schema["enum"])
            return f"Literal[{values}]"
        return "str"

    if schema_type in ("integer", "number"):
        return "int"

    if schema_type == "boolean":
        return "bool"

    if schema_type == "null":
        return "None"

    if schema_type == "array":
        item_type = json_schema_type_to_python(schema["items"], definitions)
        return f"List[{item_type}]"

    if schema_type == "object":
        # For nested objects, we'll inline them for simplicity
        # (in production, you might want to create named TypedDicts)
        return "Dict[str, Any]"

    return "Any"


def generate_definitions(definitions: Dict[str, Any]) -> str:
    """Generate Python TypedDicts for schema definitions"""
    lines = []

    for name, schema in definitions.items():
        schema_type = schema.get("type")

        if schema_type == "string" and "enum" in schema:
            # Generate Literal type alias
            values = ", ".join(f'"{v}"' for v in schema["enum"])
            lines.append(f"{name} = Literal[{values}]\n")

        elif schema_type == "object":
            # Generate TypedDict
            props = schema.get("properties", {})
            required = set(schema.get("required", []))

            if len(required) < len(props) and len(props) > 0:
                lines.append(f"class {name}(TypedDict, total=False):\n")
            else:
                lines.append(f"class {name}(TypedDict):\n")

            if not props:
                lines.append("    pass\n")
            else:
                # All fields
                for key, prop_schema in props.items():
                    py_type = json_schema_type_to_python(prop_schema, definitions)
                    lines.append(f"    {key}: {py_type}\n")

            lines.append("\n")

    return "".join(lines)


def generate_command_payloads(commands: Dict[str, Any], definitions: Dict[str, Any]) -> str:
    """Generate TypedDicts for command payloads"""
    lines = []
    lines.append("# Command Payloads\n\n")

    for name, command_schema in commands.items():
        payload_type_name = f"{name}Payload"
        payload_schema = command_schema["payload"]
        props = payload_schema.get("properties", {})
        required = set(payload_schema.get("required", []))

        if not props:
            # Empty payload
            lines.append(f"class {payload_type_name}(TypedDict):\n")
            lines.append("    pass\n")
        else:
            # Generate TypedDict with proper required/optional handling
            has_optional = len(required) < len(props)

            if has_optional:
                lines.append(f"class {payload_type_name}(TypedDict, total=False):\n")
            else:
                lines.append(f"class {payload_type_name}(TypedDict):\n")

            for key, prop_schema in props.items():
                py_type = json_schema_type_to_python(prop_schema, definitions)
                lines.append(f"    {key}: {py_type}\n")

        lines.append("\n")

    # Generate CommandType literal
    command_names = ", ".join(f'"{name}"' for name in commands.keys())
    lines.append(f"CommandType = Literal[{command_names}]\n\n")

    return "".join(lines)


def generate_event_payloads(events: Dict[str, Any], definitions: Dict[str, Any]) -> str:
    """Generate TypedDicts for event payloads"""
    lines = []
    lines.append("# Event Payloads\n\n")

    for name, event_schema in events.items():
        payload_type_name = f"{name}Payload"
        payload_schema = event_schema["payload"]
        props = payload_schema.get("properties", {})
        required = set(payload_schema.get("required", []))

        if not props:
            # Empty payload
            lines.append(f"class {payload_type_name}(TypedDict):\n")
            lines.append("    pass\n")
        else:
            has_optional = len(required) < len(props)

            if has_optional:
                lines.append(f"class {payload_type_name}(TypedDict, total=False):\n")
            else:
                lines.append(f"class {payload_type_name}(TypedDict):\n")

            for key, prop_schema in props.items():
                py_type = json_schema_type_to_python(prop_schema, definitions)
                lines.append(f"    {key}: {py_type}\n")

        lines.append("\n")

    # Generate EventType literal
    event_names = ", ".join(f'"{name}"' for name in events.keys())
    lines.append(f"EventType = Literal[{event_names}]\n")

    return "".join(lines)


def main():
    print("🔨 Generating Python types from protocol schema...")

    # Read schema
    with open(SCHEMA_PATH, "r") as f:
        schema = json.load(f)

    # Generate code
    header = '''"""
AUTO-GENERATED FILE - DO NOT EDIT

This file is generated from schemas/protocol.json
Run 'poetry run python tools/generate_types.py' to regenerate
"""

from typing import Any, Dict, List, Literal, TypedDict

'''

    definitions = generate_definitions(schema["definitions"])
    commands = generate_command_payloads(schema["commands"], schema["definitions"])
    events = generate_event_payloads(schema["events"], schema["definitions"])

    output = header + definitions + "\n" + commands + "\n" + events

    # Write output
    with open(OUTPUT_PATH, "w") as f:
        f.write(output)

    print(f"✅ Generated Python types: {OUTPUT_PATH}")
    print(f"   - {len(schema['definitions'])} definitions")
    print(f"   - {len(schema['commands'])} commands")
    print(f"   - {len(schema['events'])} events")


if __name__ == "__main__":
    main()
