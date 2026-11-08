from pathlib import Path
import re
import yaml


def _workflow(path: str) -> dict:
    document = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    assert isinstance(document, dict)
    return document


def _on(document: dict) -> dict:
    value = document.get("on", document.get(True))
    assert isinstance(value, dict)
    return value


def test_execution_workflow_is_manual_only_and_fail_closed():
    path = ".github/workflows/s6-isolated-execution.yml"
    document = _workflow(path)
    triggers = _on(document)
    assert set(triggers) == {"workflow_dispatch"}
    inputs = triggers["workflow_dispatch"]["inputs"]
    assert inputs["trial_count"]["options"] == ["300"]
    assert inputs["s6_cohort_id"]["options"] == ["s6-v23-rebuild-20261105"]
    assert inputs["c100_cohort_id"]["options"] == ["c100-v23-rebuild-20261105"]
    assert document["permissions"] == {"contents": "read"}
    assert document["concurrency"]["cancel-in-progress"] is False
    assert document["jobs"]["s6-initial-checkpoint"]["environment"]["name"] == "s6-simulation-execution"
    assert document["jobs"]["c100-initial-golden"]["environment"]["name"] == "s6-simulation-execution"
    source = Path(path).read_text(encoding="utf-8")
    assert "--require-hashes" in source
    assert "S6_EXECUTION_ENVIRONMENT_LOCKED" in source
    assert "S6_OWNER_EXECUTION_DECISION_ID" in source
    assert "EXECUTION_FAILURE.json" in source
    assert "git push" not in source
    assert "git commit" not in source


def test_security_workflow_has_read_only_permissions_and_pinned_actions():
    path = ".github/workflows/s6-security-scan.yml"
    document = _workflow(path)
    assert document["permissions"]["contents"] == "read"
    assert document["permissions"]["pull-requests"] == "read"
    source = Path(path).read_text(encoding="utf-8")
    refs = re.findall(r"uses:\s*[^@\s]+@([0-9a-f]{40})", source)
    assert len(refs) >= 2
    assert "GITLEAKS_ENABLE_COMMENTS: \"false\"" in source
    assert "GITLEAKS_ENABLE_UPLOAD_ARTIFACT: \"false\"" in source


def test_safe_identity_workflow_actions_are_full_sha_pinned():
    path = ".github/workflows/s6-explicit-cohort-identity-contract.yml"
    source = Path(path).read_text(encoding="utf-8")
    refs = re.findall(r"uses:\s*[^@\s]+@([0-9a-f]{40})", source)
    assert len(refs) >= 3


def test_runtime_dependency_lock_has_exact_versions_and_sha256_hashes():
    source = Path("requirements-lock-py311-hashed.txt").read_text(encoding="utf-8")
    entries = [line.strip() for line in source.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    assert len(entries) == 15
    assert all(re.fullmatch(r"[a-z0-9][a-z0-9._-]*==[A-Za-z0-9.!+_-]+ --hash=sha256:[0-9a-f]{64}", line) for line in entries)
    assert len({line.split("==", 1)[0] for line in entries}) == len(entries)


def test_safe_test_workflow_installs_with_hash_verification():
    source = Path(".github/workflows/s6-explicit-cohort-identity-contract.yml").read_text(encoding="utf-8")
    assert "--require-hashes -r requirements-lock-py311-hashed.txt" in source
    assert "diff -u requirements-lock-py311-hashed.txt" in source


def test_execution_workflow_pins_model_source_separately_from_workflow_head():
    source = Path(".github/workflows/s6-isolated-execution.yml").read_text(encoding="utf-8")
    assert "ac0d009aa004976009ed01e97f96d019945e9ad6" in source
    assert "S6_EXECUTION_APPROVED_WORKFLOW_SHA" in source
    assert "path: execution-source" in source
    assert 'test "$GITHUB_SHA" = "$S6_SOURCE_SHA"' not in source
    assert 'test "$GITHUB_SHA" = "$S4_SOURCE_SHA"' not in source
