import copy
import unittest

from enrollment_district_config import prepare_export


class DistrictConfigurationTest(unittest.TestCase):
    def setUp(self):
        self.export = {
            "module_config": {
                "unrelated": True,
                "benefit_plan_creation_defaults": {
                    "common": {"beneficiary_data_schema": {"properties": {"validation_status": {"type": "string"}}}},
                    "GROUP": {"json_ext": {"advanced_criteria": {"ACTIVE": [{"field": "validation_status", "value": "VERIFIED"}]}}},
                },
            },
            "phases": [
                {"id": "a", "type": "GROUP", "beneficiary_data_schema": {"properties": {"score": {"type": "integer"}}}, "json_ext": {"preserved": True}},
                {"id": "b", "type": "INDIVIDUAL", "beneficiary_data_schema": {}},
            ],
        }

    def test_targeted_merge_preserves_criteria_and_is_idempotent(self):
        original = copy.deepcopy(self.export)
        result = prepare_export(self.export, ["a"])
        self.assertEqual(self.export, original)
        self.assertEqual(result["phases"][0]["beneficiary_data_schema"]["properties"],
                         {"score": {"type": "integer"}, "district_id": {"type": "integer"}})
        self.assertEqual(result["phases"][0]["json_ext"], original["phases"][0]["json_ext"])
        self.assertEqual(result["phases"][1], original["phases"][1])
        defaults = result["module_config"]["benefit_plan_creation_defaults"]
        self.assertEqual(defaults["common"], original["module_config"]["benefit_plan_creation_defaults"]["common"])
        self.assertEqual(defaults["GROUP"]["json_ext"], original["module_config"]["benefit_plan_creation_defaults"]["GROUP"]["json_ext"])
        self.assertEqual(result, prepare_export(result, ["a"]))

    def test_no_phase_ids_changes_only_creation_defaults(self):
        self.assertEqual(prepare_export(self.export, [])["phases"], self.export["phases"])

    def test_unknown_individual_and_conflicting_fields_fail(self):
        for ids in (["unknown"], ["b"]):
            with self.assertRaises(ValueError):
                prepare_export(self.export, ids)
        self.export["phases"][0]["beneficiary_data_schema"] = {"properties": {"district_id": {"type": "string"}}}
        with self.assertRaises(ValueError):
            prepare_export(self.export, ["a"])

    def test_string_schema_and_existing_metadata_preserved(self):
        self.export["phases"][0]["beneficiary_data_schema"] = '{"properties":{"district_id":{"type":"integer","description":"keep"}}}'
        result = prepare_export(self.export, ["a"])
        self.assertEqual(result["phases"][0]["beneficiary_data_schema"]["properties"]["district_id"]["description"], "keep")


if __name__ == "__main__":
    unittest.main()
