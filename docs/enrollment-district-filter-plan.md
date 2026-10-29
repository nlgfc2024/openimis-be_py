# Household enrollment district filter: openimis-be_py

Status: implementation planning only. This branch currently contains documentation, not a working district filter.

## Branch and ownership

- Base: `mw/develop`; do not branch from the repository default if it differs.
- Feature branch: `feature/enrollment-district-filter-rollout`.
- Assignee: @YutakaX17.
- Requested reviewers: @mcleanka, @uniquedj95, @Lenwell89.
- Target project: https://github.com/orgs/nlgfc2024/projects/12 (added; initial status: To Do).

## Behavior and shared contract

Keep the phase criterion `validation_status = VERIFIED` locked during enrollment. Under Add filters, offer `Location – District (R) | Equals | [Select district]` as an optional household operator filter. Select from active location master data within permitted scope, not a hard-coded list.

Use the schema property `district_id: {"type":"integer"}` on GROUP phases. A selected numeric database location ID serializes as `district_id__exact__integer=123`. An empty/cleared/removed selection contributes no condition. Do not put district in saved phase advanced_criteria, use an all-district sentinel, or duplicate district data in household json_ext.

The backend must use Group.location and district ancestry, intersect with authenticated user scope before eligibility counts/ranking, retain VERIFIED and existing phase-wide capacity rules, and apply identical rules to summary, preview and confirmation. A selected R can match its active descendants at any depth. No district selection must never disable access restrictions. Confirmation revalidates current eligibility.

## Small reviewable commits

Issue order below is the intended commit sequence in this repository. Each implementation commit includes its focused regression tests and references its issue. Record actual test commands/results and commit SHA in the issue; do not mark work complete based on this planning file.

### APP-BE-1: Integrate the district enrollment backend module on mw/develop

Issue: https://github.com/nlgfc2024/openimis-be_py/issues/15

Suggested commit: `build(enrollment): integrate district filtering backend`

After backend module changes merge, update the assembly's actual dependency manifests/lock references using its existing dependency convention. Inspect the installed Social Protection default-merging implementation and verify GROUP schema overrides support district_id plus validation_status. Reconcile upstream enrollment refactors before updating dependencies; do not include unrelated upgrades.

Acceptance:

- [ ] Assembly resolves the reviewed backend module revision/version reproducibly.
- [ ] Installed Social Protection supports the documented GROUP default schema contract, or a narrowly scoped dependency issue is opened before rollout.
- [ ] Backend startup and relevant enrollment integration checks pass with recorded commands and results.

Dependencies: https://github.com/nlgfc2024/openimis-be-individual_py/issues/21.

### APP-BE-2: Prepare reversible district filter defaults and existing-phase rollout

Issue: https://github.com/nlgfc2024/openimis-be_py/issues/16

Suggested commit: `docs(enrollment): document district configuration rollout`

Add a repository-native configuration fixture/runbook for GROUP beneficiary_data_schema containing validation_status:string and district_id:integer. Keep VERIFIED criteria for POTENTIAL/ACTIVE unchanged and never add district to mandatory criteria. Document export, targeted existing-phase schema merge, dry-run/idempotence where scripted, verification and rollback. Do not apply production configuration as part of this planning task.

Acceptance:

- [ ] New phases expose optional district filtering without altering existing eligibility.
- [ ] Existing phase update preserves every unrelated schema property and criterion.
- [ ] No hard-coded district list, all-district sentinel or duplicate json_ext district data is introduced.
- [ ] Rollout requires deployed code support and records restricted/broad user validation and rollback steps.

Dependencies: https://github.com/nlgfc2024/openimis-be_py/issues/15, https://github.com/nlgfc2024/openimis-fe_js/issues/10.

## Cross-repository integration and review

- BE-1: https://github.com/nlgfc2024/openimis-be-individual_py/issues/19
- BE-2: https://github.com/nlgfc2024/openimis-be-individual_py/issues/20
- BE-3: https://github.com/nlgfc2024/openimis-be-individual_py/issues/21
- FE-1: https://github.com/nlgfc2024/openimis-fe-individual_js/issues/23
- FE-2: https://github.com/nlgfc2024/openimis-fe-individual_js/issues/24
- FE-3: https://github.com/nlgfc2024/openimis-fe-individual_js/issues/25
- CORE-1: https://github.com/nlgfc2024/openimis-fe-core_js/issues/25
- APP-FE-1: https://github.com/nlgfc2024/openimis-fe_js/issues/9
- APP-FE-2: https://github.com/nlgfc2024/openimis-fe_js/issues/10

Backend and frontend module work must merge before assembly references are updated. Staging uses test configuration; production defaults and existing-phase schema updates follow successful integrated acceptance. Preserve unrelated schema properties, document export/rollback, and avoid applying production configuration in this planning PR.

Check current enrollment refactors before implementation: backend PRs https://github.com/nlgfc2024/openimis-be-individual_py/pull/8, https://github.com/nlgfc2024/openimis-be-individual_py/pull/17 and https://github.com/nlgfc2024/openimis-be-individual_py/pull/18, and frontend PR https://github.com/nlgfc2024/openimis-fe-individual_js/pull/22. Rebase on current mw/develop and adapt paths if enrollment ownership moves; do not merge unrelated work into this feature merely to avoid resolving overlap.

Keep commits separated by issue for reviewer navigation. Add new commits for review fixes where practical; no implementation issue is closed by the initial documentation commit. Before marking the feature ready, update the PR description to describe actual delivered behavior, actual validation, remaining risks, and completed issue links. Since mw/develop may not be the repository default branch, verify issue closure explicitly after implementation is merged rather than relying solely on automatic closing keywords.

## Opened PRs

- openimis-be-individual_py: https://github.com/nlgfc2024/openimis-be-individual_py/pull/22
- openimis-fe-individual_js: https://github.com/nlgfc2024/openimis-fe-individual_js/pull/26
- openimis-fe-core_js: https://github.com/nlgfc2024/openimis-fe-core_js/pull/26
- openimis-be_py: https://github.com/nlgfc2024/openimis-be_py/pull/17
- openimis-fe_js: https://github.com/nlgfc2024/openimis-fe_js/pull/11

Initial mw/develop commit for this repository: `ef8b985ac2363330228d7be3043fdbaab5290dd2`.

