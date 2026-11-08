from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / ".github/workflows/s6-archive-recovery-release.yml"


def bash(script: str) -> str:
    result = subprocess.run(
        ["bash", "-euo", "pipefail", "-c", script],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


class S6ReleaseWorkflowParsingTests(unittest.TestCase):
    def test_missing_release_is_zero_matches(self):
        out = bash(r'''
          matches=""
          match_count="$(printf '%s\n' "$matches" | awk 'NF {n++} END {print n+0}')"
          [[ "$match_count" == "0" ]]
          printf '%s' "$match_count"
        ''')
        self.assertEqual(out, "0")

    def test_existing_release_fields_parse_as_tab_separated_values(self):
        out = bash(r'''
          matches=$'437946401\ttrue\tf2ffb9743c8b9aff9fd9d4cadcdb5484e6069866'
          match_count="$(printf '%s\n' "$matches" | awk 'NF {n++} END {print n+0}')"
          [[ "$match_count" == "1" ]]
          IFS=$'\t' read -r release_id is_draft target_commit <<< "$matches"
          printf '%s|%s|%s' "$release_id" "$is_draft" "$target_commit"
        ''')
        self.assertEqual(
            out,
            "437946401|true|f2ffb9743c8b9aff9fd9d4cadcdb5484e6069866",
        )

    def test_multiple_release_records_are_rejected_by_count(self):
        out = bash(r'''
          matches=$'1\ttrue\tsha1\n2\ttrue\tsha2'
          match_count="$(printf '%s\n' "$matches" | awk 'NF {n++} END {print n+0}')"
          [[ "$match_count" == "2" ]]
          printf '%s' "$match_count"
        ''')
        self.assertEqual(out, "2")

    def test_github_output_is_written_as_a_real_line(self):
        out = bash(r'''
          release_id=437946401
          output_file="$(mktemp)"
          printf 'release_id=%s\n' "$release_id" > "$output_file"
          grep -Fx 'release_id=437946401' "$output_file"
          rm -f "$output_file"
        ''')
        self.assertEqual(out, "release_id=437946401")

    def test_tag_lookup_only_allows_200_or_404_and_fails_closed_otherwise(self):
        out = bash(r'''
          classify() {
            local response="$1"
            if grep -qE '^HTTP/[0-9.]+ 200' <<< "$response"; then
              printf present
            elif grep -qE '^HTTP/[0-9.]+ 404' <<< "$response"; then
              printf missing
            else
              printf fail_closed
            fi
          }
          [[ "$(classify 'HTTP/2 200 OK')" == present ]]
          [[ "$(classify 'HTTP/2 404 Not Found')" == missing ]]
          [[ "$(classify 'HTTP/2 403 Forbidden')" == fail_closed ]]
          [[ "$(classify 'HTTP/2 500 Server Error')" == fail_closed ]]
          printf PASS
        ''')
        self.assertEqual(out, "PASS")

    def test_workflow_uses_single_backslash_escape_sequences(self):
        workflow = WORKFLOW_PATH.read_text()
        self.assertIn(r'''printf '%s\n' "$matches"''', workflow)
        self.assertIn(r'''IFS=$'\t' read -r release_id''', workflow)
        self.assertIn(r'''printf 'release_id=%s\n' "$release_id"''', workflow)
        self.assertIn(r'''printf '%s\n' "$tag_http"''', workflow)
        self.assertNotIn(r'''printf '%s\\n' "$matches"''', workflow)
        self.assertNotIn(r'''IFS=$'\\t' read -r release_id''', workflow)
        self.assertNotIn(r'''printf 'release_id=%s\\n' "$release_id"''', workflow)
        self.assertNotIn(r'''printf '%s\\n' "$tag_http"''', workflow)
        self.assertIn("^HTTP/[0-9.]+ 404", workflow)
        self.assertIn("Tag lookup failed for a reason other than 404", workflow)


if __name__ == "__main__":
    unittest.main(verbosity=2)
