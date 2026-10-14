import csv
import pytest
from bloon_audit.core import export_csv, generate_report, load_data, validate_all
from bloon_audit.validation import REQUIRED_FINDING_FIELDS, ValidationError, build_evidence_registry, validate_finding

VALID_EVIDENCE = {"evidence_id":"E1","title":"Title","issuing_org":"Issuer","url":"https://example.com/source","access_date":"2024-01-01","is_verifiable":True,"establishes":"A documented claim","unknowns":"Other claims unknown"}
VALID_FINDING = {"finding_id":"F1","project_id":"P1","domain":"civil","category":"Structure","requirement":"Requirement","observation":"Observation","evidence_ids":["E1"],"source_url":"https://example.com/source","source_document":"Document","source_date":"2024-01-01","observation_date":"2024-01-02","verification_status":"verified","severity":"high","confidence":0.9,"limitations":"Limitations","reviewer_notes":"Notes"}

@pytest.mark.parametrize("bad", [[], {}, None, 123])
def test_enum_bad_types_do_not_crash(bad):
    for field in ("domain", "verification_status", "severity"):
        finding = VALID_FINDING.copy(); finding[field] = bad
        with pytest.raises(ValidationError): validate_finding(finding, 0, {"E1": VALID_EVIDENCE})

def test_evidence_date_url_and_boolean_validation():
    for field, value in (("access_date", "2023-02-30"), ("url", "ftp://example.com"), ("is_verifiable", "yes")):
        evidence = VALID_EVIDENCE.copy(); evidence[field] = value
        with pytest.raises(ValidationError): build_evidence_registry([evidence])

def test_evidence_required_fields_and_duplicate_ids():
    with pytest.raises(ValidationError): build_evidence_registry([{"evidence_id":"E1"}])
    with pytest.raises(ValidationError, match="Duplicate"): build_evidence_registry([VALID_EVIDENCE, VALID_EVIDENCE])

def test_unknown_evidence_reference_rejected():
    finding = VALID_FINDING.copy(); finding["evidence_ids"] = ["NOPE"]
    with pytest.raises(ValidationError, match="Unknown evidence_id"): validate_finding(finding, 0, {"E1": VALID_EVIDENCE})

def test_confidence_edge_cases():
    for value in (True, float("nan"), float("inf"), -0.1, 1.1, "0.5"):
        finding = VALID_FINDING.copy(); finding["confidence"] = value
        with pytest.raises(ValidationError): validate_finding(finding, 0, {"E1": VALID_EVIDENCE})

def test_csv_special_characters_roundtrip(tmp_path):
    finding = VALID_FINDING.copy(); finding["observation"] = 'quotes " commas, and\nnewlines'
    path = tmp_path / "out.csv"; export_csv([finding], str(path))
    loaded = load_data(str(path))
    assert loaded[0]["observation"] == finding["observation"]
    assert loaded[0]["evidence_ids"] == ["E1"]

def test_csv_export_deterministic_and_canonical(tmp_path):
    first = VALID_FINDING.copy(); first["finding_id"] = "F2"
    second = VALID_FINDING.copy(); second["finding_id"] = "F1"
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    export_csv([first, second], str(a)); export_csv([second, first], str(b))
    assert a.read_bytes() == b.read_bytes()
    assert next(csv.reader(a.open(encoding="utf-8"))) == REQUIRED_FINDING_FIELDS
    with pytest.raises(ValueError, match="canonical order"):
        export_csv([first], str(tmp_path / "bad.csv"), schema_fields=list(reversed(REQUIRED_FINDING_FIELDS)))

def test_empty_export_has_canonical_header(tmp_path):
    path = tmp_path / "empty.csv"; export_csv([], str(path))
    assert next(csv.reader(path.open(encoding="utf-8"))) == REQUIRED_FINDING_FIELDS
    assert load_data(str(path)) == []

def test_malformed_json_and_csv_are_reported(tmp_path):
    path = tmp_path / "bad.json"; path.write_text("{bad", encoding="utf-8")
    with pytest.raises(ValueError, match="Malformed"): load_data(str(path))
    path = tmp_path / "bad.csv"; path.write_text("finding_id,confidence\nF1,nope\n", encoding="utf-8")
    with pytest.raises(ValueError, match="numeric"): load_data(str(path))

def test_duplicate_finding_ids_rejected():
    assert any("Duplicate finding_id" in error for error in validate_all([VALID_FINDING, VALID_FINDING], {"E1": VALID_EVIDENCE}))

def test_report_is_traceable_and_deterministic(tmp_path):
    a, b = tmp_path / "a.md", tmp_path / "b.md"
    generate_report([VALID_FINDING], str(a), timestamp="2026-01-01", evidence_registry={"E1": VALID_EVIDENCE})
    generate_report([VALID_FINDING], str(b), timestamp="2026-01-01", evidence_registry={"E1": VALID_EVIDENCE})
    content = a.read_text(encoding="utf-8")
    assert a.read_bytes() == b.read_bytes()
    for label in ("Project ID", "Requirement", "Source Document", "Source URL", "Limitations", "Reviewer Notes", "Establishes", "Unknowns"):
        assert label in content

def test_missing_information_is_not_failure():
    finding = VALID_FINDING.copy(); finding.update(verification_status="unverified", severity="undetermined", confidence=0.1, observation="The relevant document has not been acquired.")
    validate_finding(finding, 0, {"E1": VALID_EVIDENCE})

def test_iso_date_rejects_suffix_and_impossible_date():
    for date in ("2024-01-01junk", "2023-02-30"):
        finding = VALID_FINDING.copy(); finding["source_date"] = date
        with pytest.raises(ValidationError): validate_finding(finding, 0, {"E1": VALID_EVIDENCE})
