# Optional district enrollment rollout

Runtime dependencies: the individual module revision pinned in `openimis.json` implements `district_id__exact__integer=<numeric R ID>`. Merge the module PR before the assembly PR; review the exact pin when rebasing. This document and the preparation script do not apply production changes.

## Configuration preparation

Export the complete Social Protection module configuration and the existing phases explicitly selected for this rollout. Keep an untouched backup. Build an input JSON object with this structure (the nested values must be your real exported data):

```json
{
  "module_config": {"benefit_plan_creation_defaults": {}},
  "phases": [{"id": "phase-uuid", "type": "GROUP", "beneficiary_data_schema": {}, "json_ext": {}}]
}
```

Run from the assembly root:

```sh
python script/enrollment_district_config.py before.json proposed.json --phase-id phase-uuid
diff -u before.json proposed.json
python -m unittest discover -s script -p 'test_enrollment_district_config.py'
```

Repeat `--phase-id` for each intended GROUP phase. Without IDs, only GROUP creation defaults change. The script uses no database, performs no API writes, refuses to overwrite any existing output file, rejects conflicting field types and unknown/non-GROUP phase IDs, and is idempotent at the JSON content level.

Review that the only semantic additions are `district_id: {"type":"integer"}` and any missing object-schema containers. Existing schema fields, phase criteria, ranking, and unrelated module settings must be preserved. The installed Social Protection `phase_defaults.build_benefit_plan_defaults` merges common and GROUP defaults recursively, so common `validation_status` remains available when the GROUP schema adds the district field.

Keep the existing `validation_status = VERIFIED` criteria for POTENTIAL/ACTIVE. Do not add district to `advanced_criteria` or system mandatory criteria. The script deliberately does not create or rewrite eligibility rules; verify VERIFIED is already configured on the phases intended to use that rule. No household JSON backfill or database migration is required.

## Deployment and acceptance

1. Review/merge the backend, frontend individual, and core module PRs. Deploy the assembled code with the exact accepted pins before exposing the field.
2. In staging, apply the reviewed `module_config` through the existing module configuration administration path. Update only each selected phase's beneficiary data schema using its supported update path; the exported wrapper is a preparation format, not a bulk API payload. Do not overwrite phase `json_ext` or concurrent edits. Re-export and compare before applying if another administrator changed the source.
3. Enable the existing frontend `individual.enrollmentUiConfig.show_advanced_operator_filters` and `show_mandatory_criteria_summary` settings (both default true).
4. Verify new GROUP phases expose District (R). Verify targeted existing phases expose it and unrelated phases/schemas are unchanged.
5. Test selected district, no district, cleared district, and phase/status changes with broad and restricted users. Check names/IDs, summary, list, and confirmation; require a new preview after changes. Verify forbidden district API requests fail and phase-wide capacity does not reset per district.
6. Record staging versions, results, and reviewer approval before the production configuration update. No production or staging rollout was executed by the implementation commits themselves.

## Rollback

Export current state again. Restore only the configuration/schema additions from the saved pre-change export, preserving intervening unrelated edits. Remove saved district operator selections before reverting backend code that does not understand the field. Revert assembly pins through a reviewed PR. Never remove VERIFIED rules or location access controls during rollback.

## Validation performed during implementation

- The backend district and authoritative enrollment suites pass 43 tests on isolated PostgreSQL 16 with row security exercised, an in-memory task broker and test-only database schema synchronization.
- The preparation script is covered for preservation, explicit targeting, repeated execution, unsupported phase types, conflicting properties, and string schemas.
- The installed Social Protection common/GROUP merge implementation was inspected and exercised locally. Shared location helpers and the existing Group missing-location/technical-user policies are retained.
- Deployment-specific configuration, real staging accounts, and production data are not covered by the isolated test run; complete the acceptance steps above before rollout.
