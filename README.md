# BLOON_AUDIT_DATACENTER v0.1.1

Evidence-based preliminary screening framework for data-center project documentation.

**Core rule: Missing Information ≠ Technical Failure.** A missing document is an evidence gap, not proof of technical failure or regulatory non-compliance.

## Scope

The tool validates structured findings and evidence references, then produces deterministic CSV exports and traceable Markdown reports. It is not a substitute for qualified engineering review, site inspection, authenticated-document verification, or a regulator's decision.

## Setup

Python 3.10+ is required.

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e '.[test]'
python -m pytest -v
```

## CLI

```bash
python -m bloon_audit validate data/processed/findings.json --evidence data/processed/evidence.json
python -m bloon_audit report data/processed/findings.json --evidence data/processed/evidence.json --output reports/audit.md
python -m bloon_audit export data/processed/findings.json --evidence data/processed/evidence.json --output data/processed/findings_export.csv
```

Exit codes: `0` success, `1` input/data error, `2` unexpected runtime error.

## Case-study limitations

The included DCI example is a research scaffold, not an engineering conclusion. The exact target facility remains unresolved. A corporate portfolio page does not establish facility-specific AMDAL status, structural design, UPS topology, water consumption, PUE, or regulatory compliance. Do not treat a placeholder URL as evidence. See `docs/CASE_STUDY.md` and `docs/METHODOLOGY.md`.
