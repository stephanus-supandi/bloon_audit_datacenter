import csv
import json
import os
from datetime import datetime
from .validation import REQUIRED_FINDING_FIELDS, ValidationError, validate_finding


def load_json(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as stream:
            data = json.load(stream)
    except FileNotFoundError:
        raise
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError(f"Malformed or non-UTF-8 JSON in {filepath}: {exc}") from exc
    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        return data
    raise ValueError(f"JSON root in {filepath} must be an array or object")


def load_csv(filepath):
    data = []
    try:
        with open(filepath, "r", encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream, strict=True)
            if reader.fieldnames is None:
                return []
            for row_num, row in enumerate(reader, start=2):
                if None in row:
                    raise ValueError(f"Malformed CSV at row {row_num}: extra fields without headers")
                if "evidence_ids" in row and isinstance(row["evidence_ids"], str):
                    raw = row["evidence_ids"].strip()
                    if raw.startswith("["):
                        try:
                            parsed = json.loads(raw)
                        except json.JSONDecodeError as exc:
                            raise ValueError(f"Malformed JSON in CSV evidence_ids at row {row_num}: {exc}") from exc
                        if not isinstance(parsed, list):
                            raise ValueError(f"CSV evidence_ids at row {row_num} must encode a JSON list")
                        row["evidence_ids"] = parsed
                    else:
                        row["evidence_ids"] = [part.strip() for part in raw.split(",") if part.strip()]
                if "confidence" in row and row["confidence"] not in (None, ""):
                    try:
                        row["confidence"] = float(row["confidence"])
                    except ValueError as exc:
                        raise ValueError(f"Malformed CSV at row {row_num}: confidence must be numeric") from exc
                data.append(row)
    except FileNotFoundError:
        raise
    except UnicodeDecodeError as exc:
        raise ValueError(f"Encoding error in {filepath}: {exc}") from exc
    except csv.Error as exc:
        raise ValueError(f"Malformed CSV structure in {filepath}: {exc}") from exc
    return data


def load_data(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    suffix = os.path.splitext(filepath)[1].lower()
    if suffix == ".json":
        return load_json(filepath)
    if suffix == ".csv":
        return load_csv(filepath)
    raise ValueError("Unsupported file format. Use .json or .csv")


def validate_all(findings, evidence_registry):
    errors, seen = [], set()
    for index, finding in enumerate(findings):
        try:
            validate_finding(finding, index, evidence_registry)
            fid = finding["finding_id"]
            if fid in seen:
                errors.append(f"Duplicate finding_id {fid!r} at index {index}")
            seen.add(fid)
        except ValidationError as exc:
            errors.append(str(exc))
    return errors


def _md(value):
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def generate_report(findings, output_path, timestamp=None, evidence_registry=None):
    timestamp = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8", newline="") as out:
        out.write("# Audit Report: Data Center Preliminary Screening\n\n")
        out.write(f"**Generated:** {_md(timestamp)}  \n**Total findings:** {len(findings)}\n\n")
        out.write("> Preliminary document-based screening only. Missing information is not proof of technical failure or regulatory non-compliance.\n\n")
        out.write("## Detailed findings\n\n")
        for finding in sorted(findings, key=lambda item: item["finding_id"]):
            out.write(f"### {_md(finding['finding_id'])} — {_md(finding['category'])}\n\n")
            for field, label in [
                ("project_id", "Project ID"), ("domain", "Domain"), ("requirement", "Requirement"),
                ("observation", "Observation"), ("verification_status", "Verification Status"),
                ("severity", "Severity"), ("confidence", "Confidence"), ("source_document", "Source Document"),
                ("source_url", "Source URL"), ("source_date", "Source Date"), ("observation_date", "Observation Date"),
                ("limitations", "Limitations"), ("reviewer_notes", "Reviewer Notes")]:
                out.write(f"- **{label}:** {_md(finding.get(field) if finding.get(field) is not None else 'N/A')}\n")
            out.write(f"- **Evidence refs:** {_md(', '.join(finding.get('evidence_ids', [])))}\n")
            for eid in finding.get("evidence_ids", []):
                evidence = (evidence_registry or {}).get(eid, {})
                out.write(f"  - **{_md(eid)} — {_md(evidence.get('title', 'N/A'))}:** {_md(evidence.get('url', 'N/A'))}\n")
                out.write(f"    - Establishes: {_md(evidence.get('establishes', 'N/A'))}\n")
                out.write(f"    - Unknowns: {_md(evidence.get('unknowns', 'N/A'))}\n")
            out.write("\n---\n\n")


def export_csv(findings, output_path, schema_fields=None):
    columns = list(REQUIRED_FINDING_FIELDS)
    if schema_fields is not None and list(schema_fields) != columns:
        raise ValueError("schema_fields must match REQUIRED_FINDING_FIELDS in canonical order")
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for finding in sorted(findings, key=lambda item: item.get("finding_id", "")):
            row = {key: finding.get(key, "") for key in columns}
            if isinstance(row["evidence_ids"], list):
                row["evidence_ids"] = json.dumps(row["evidence_ids"], ensure_ascii=False, separators=(",", ":"))
            writer.writerow(row)
