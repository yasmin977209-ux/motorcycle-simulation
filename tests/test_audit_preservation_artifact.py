import unittest

from scripts.audit_preservation_artifact import (
    classify_audit,
    missing_required_accounting_fields,
    REQUIRED_ACCOUNTING_FIELDS,
)

class D0FailClosedAuditTests(unittest.TestCase):
    def test_missing_source_metadata_blocks_when_required(self):
        self.assertEqual(classify_audit("MISSING_EVIDENCE", "PASS_SCOPED", True), "BLOCKED")

    def test_mismatched_source_metadata_blocks_when_required(self):
        self.assertEqual(classify_audit("FAIL", "PASS_SCOPED", True), "BLOCKED")

    def test_missing_metadata_is_not_promoted_when_not_required(self):
        self.assertEqual(classify_audit("MISSING_EVIDENCE", "PASS_SCOPED", False), "PASS_SCOPED")

    def test_missing_parquet_blocks(self):
        self.assertEqual(classify_audit("PASS", "MISSING_EVIDENCE", True), "BLOCKED")

    def test_all_five_accounting_fields_are_required(self):
        missing=missing_required_accounting_fields([{"name":"Net_Equity"},{"name":"Capital"}])
        self.assertEqual(set(missing), REQUIRED_ACCOUNTING_FIELDS)

    def test_field_check_is_case_insensitive_but_does_not_alias(self):
        columns=[{"name":name.lower()} for name in REQUIRED_ACCOUNTING_FIELDS]
        self.assertEqual(missing_required_accounting_fields(columns), [])

if __name__=="__main__":
    unittest.main()
