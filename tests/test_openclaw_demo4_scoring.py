"""Guard the live demo4 case against stale seeded-mailbox scoring."""

import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1] / "submissions" / "openclaw-forge"


def _judge(name):
    config = yaml.safe_load((ROOT / "eval.yaml").read_text())
    judge = next(j for j in config["judges"] if j["name"] == name)
    namespace = {}
    source = "def check(outputs, arguments):\n" + "".join(
        "    " + line + "\n" for line in judge["check"].splitlines()
    )
    exec(compile(source, "<judge>", "exec"), namespace)
    return namespace["check"]


def test_scene_and_active_case_use_labeled_demo4_mailbox():
    scene = yaml.safe_load((ROOT / "scenes" / "monday-acquisition.yaml").read_text())
    annotations = yaml.safe_load(
        (ROOT / "cases-morning-briefing" / "morning-briefing" / "annotations.yaml").read_text()
    )
    assert scene["m365"]["user"] == annotations["expected_mailbox"]
    assert scene["m365"]["user"] == "tbx-demo4@dev.mscloud.ibm.com"
    assert annotations["required_scope"] == "full"
    for key in ("expected_top_of_mind", "expected_excluded", "expected_fyi",
                "expected_separate", "expected_bundles"):
        assert annotations[key], key
    assert "tbx-demo2" not in json.dumps(annotations).lower()


def test_full_publication_is_required_not_just_agent_prose():
    check = _judge("published_full_brief")
    assert not check({"output_content": "I completed the briefing"}, {})
    brief = {"scope": "full", "evidenceId": "e-1", "topOfMind": [],
             "fyi": [], "lookingAhead": []}
    assert check({"output_content": json.dumps(brief)}, {})
    brief["scope"] = "attention"
    assert not check({"output_content": json.dumps(brief)}, {})


def test_coverage_requires_labeled_full_mailbox_count_in_published_brief():
    check = _judge("briefing_evidence_coverage")
    annotations = {"minimum_email_count": 347}
    brief = {"scope": "full", "coverage": [{"id": "email", "value": "347"}]}
    assert check({"output_content": json.dumps(brief), "annotations": annotations}, {})
    brief["coverage"][0]["value"] = "346"
    assert not check({"output_content": json.dumps(brief), "annotations": annotations}, {})
    assert not check({"output_content": json.dumps(brief)}, {})


def test_full_mailbox_config_is_not_a_sample_and_requires_snapshot_fingerprint():
    config = yaml.safe_load((ROOT / "eval.yaml").read_text())
    env = config["execution"]["env"]
    assert "FORGE_DIAGNOSTIC_MAIL_WINDOWS" not in env
    assert "FORGE_DIAGNOSTIC_BATCH_RECORDS" not in env
    assert len(env["FORGE_EXPECTED_MAILBOX_FINGERPRINT"]) == 64
    assert yaml.safe_load(
        (ROOT / "cases-morning-briefing" / "morning-briefing" / "annotations.yaml").read_text()
    )["minimum_email_count"] == 347
