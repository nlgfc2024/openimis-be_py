# Upstream release test fixture repairs

These patches apply only to installed test files in assembly CI. They do not
change runtime code, skip tests, or alter expected results. Remove each patch
when the assembly adopts an upstream release containing the corresponding fix.
Application fails if the expected source context no longer matches.

- `claim-batch-health-facility.patch`: release/26.04 passes an integer to the
  medical-pricelist helpers, which require a HealthFacility instance. The crash
  in setUpClass leaves the class's transaction open and contaminates later tests.
  Assign the user to the district created by this class instead of assuming demo
  districts exist, so the class also runs independently.
- `insuree-valid-replacement-photo.patch`: the update test corrupts the PNG
  signature of its second image. Use a distinct, valid blue PNG so the test
  exercises replacement of a photo rather than image-validation rejection.
- `insuree-valid-family-photo.patch`: the family update fixture has a corrupt
  PNG checksum; provide a valid replacement so its poverty update can execute.
- `payer-self-contained-fixtures.patch`: create the payer and product used by
  the funding mutation, and assign the test-created district. This avoids a
  setUpClass crash and reliance on demo records or preceding test classes.

Sources inspected: claim_batch `97458a930cbab6dc666ad85237ddb792ed0997f1`
and insuree `ebdb761f9412b926ef712c7e9578b13f466261f8`.
