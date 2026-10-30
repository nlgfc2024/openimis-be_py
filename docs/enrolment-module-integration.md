# District enrolment after module extraction

The district feature and three household summary counts now belong to the dedicated Enrolment modules. Individual and Social Protection must use compatible post-extraction revisions; do not restore the old enrolment implementations from the Individual feature branches.

The manifest pins the coordinated revisions. Backend summary fields must be deployed before the frontend requesting them. Keep frontend Core's district label revision. Existing assembly PR reviewers are preserved.

## Configuration and rollout

1. Deploy/register backend `enrolment` and frontend `EnrolmentModule` with the extracted Individual and Social Protection modules. Verify one owner for routes, GraphQL enrolment fields and approval handlers.
2. Move deployment enrolment settings into backend `enrolment` ModuleConfiguration, preserving mandatory criteria, maker-checker choices, registry mappings and approval event names. Move frontend `enrollment_ui` to Enrolment. Compatibility route/reference aliases do not automatically migrate stored configuration.
3. Keep phase creation defaults and existing phase schemas in Social Protection. Use the existing offline configuration transformer to add the GROUP integer district property without replacing other fields or VERIFIED criteria. District remains optional; no household JSON backfill is needed.
4. Verify summary/list/confirmation for selected, changed and cleared districts with broad and partial location access. Verify direct API rejection, primary-worker eligibility, current-preview confirmation, phase-wide capacity and approval after scope/eligibility changes.
5. Verify the three cards independently: eligible verified unenrolled pool before cap; stored target (zero/null included); enrolled stock within scope/district regardless of current eligibility.

## Evidence and remaining gates

Backend Enrolment suite: 90 passing tests plus 10 subtests on isolated PostgreSQL with current extracted registry and Social Protection sources; the final district suite passes 18 tests plus 10 subtests, including approval after a household changes district. Frontend: four test files and Vite library build pass. Offline configuration transformer: four tests pass.

The backend runner uses schema synchronization, in-memory caches/Celery, upstream reference fixtures and test-only password settings. These results do not claim a production migration rehearsal. Full frontend clean-install assembly build and staging browser UAT remain required before production rollout. Existing historical evidence is retained with an explicit superseded-baseline notice.

Rollback must retain a coordinated module set. Remove stored district operator selections before reverting code that does not understand the operator; preserve VERIFIED and row security. Revert configuration additions selectively without discarding intervening edits.

## Replacement module PRs

- Backend: https://github.com/nlgfc2024/openimis-be-enrolment_py/pull/2
- Frontend: https://github.com/nlgfc2024/openimis-fe-enrolment_js/pull/2
- Shared labels: https://github.com/nlgfc2024/openimis-fe-core_js/pull/26
