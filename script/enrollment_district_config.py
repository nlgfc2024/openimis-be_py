"""Prepare an offline, reviewable configuration export; never connect to a database."""
import argparse
import copy
import json
from pathlib import Path


def add_district_property(schema):
    if isinstance(schema, str):
        schema = json.loads(schema)
    if not isinstance(schema, dict):
        raise ValueError("Beneficiary schema must be a JSON object.")
    result = copy.deepcopy(schema)
    if result.get("type", "object") != "object":
        raise ValueError("Beneficiary schema must have object type.")
    result.setdefault("type", "object")
    properties = result.setdefault("properties", {})
    if not isinstance(properties, dict):
        raise ValueError("Schema properties must be an object.")
    if "district_id" in properties:
        if not isinstance(properties["district_id"], dict) or properties["district_id"].get("type") != "integer":
            raise ValueError("Existing district_id conflicts with the reserved integer filter.")
    else:
        properties["district_id"] = {"type": "integer"}
    return result


def prepare_export(export, phase_ids):
    result = copy.deepcopy(export)
    if not isinstance(result, dict) or not isinstance(result.get("module_config"), dict):
        raise ValueError("Export must contain a module_config object and phases list.")
    defaults = result["module_config"].setdefault("benefit_plan_creation_defaults", {})
    group = defaults.setdefault("GROUP", {})
    # Existing common/type criteria and all other module configuration stay intact.
    group["beneficiary_data_schema"] = add_district_property(group.get("beneficiary_data_schema", {}))
    phases = result.get("phases")
    if not isinstance(phases, list):
        raise ValueError("Export must contain a phases list.")
    selected = {str(value) for value in phase_ids}
    found = set()
    for phase in phases:
        if not isinstance(phase, dict):
            raise ValueError("Each phase must be an object.")
        identifier = str(phase.get("id"))
        if identifier not in selected:
            continue
        if identifier in found:
            raise ValueError("Duplicate phase ID in export: " + identifier)
        if phase.get("type") != "GROUP":
            raise ValueError("Selected phase is not a GROUP phase: " + identifier)
        found.add(identifier)
        phase["beneficiary_data_schema"] = add_district_property(phase.get("beneficiary_data_schema") or {})
    if found != selected:
        raise ValueError("Unknown phase IDs: " + ", ".join(sorted(selected - found)))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Exported module_config and phases JSON")
    parser.add_argument("output", type=Path, help="New output file; existing files are never overwritten")
    parser.add_argument("--phase-id", action="append", default=[], help="Explicit existing GROUP phase ID; repeat as needed")
    args = parser.parse_args()
    try:
        prepared = prepare_export(json.loads(args.input.read_text()), args.phase_id)
        with args.output.open("x") as target:
            json.dump(prepared, target, indent=2, ensure_ascii=False)
            target.write("\n")
    except (ValueError, TypeError, AttributeError, OSError) as error:
        parser.exit(2, f"Cannot prepare district configuration: {error}\n")


if __name__ == "__main__":
    main()
