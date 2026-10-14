import argparse
import sys
from .core import export_csv, generate_report, load_data, validate_all
from .validation import REQUIRED_FINDING_FIELDS, ValidationError, build_evidence_registry


def main():
    parser = argparse.ArgumentParser(prog="bloon_audit")
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("validate", "report", "export"):
        item = sub.add_parser(command)
        item.add_argument("findings_file")
        item.add_argument("--evidence", required=True)
        if command in {"report", "export"}:
            item.add_argument("--output", "-o", required=True)
        if command == "report":
            item.add_argument("--timestamp")
    args = parser.parse_args()
    try:
        findings = load_data(args.findings_file)
        evidence = build_evidence_registry(load_data(args.evidence))
        errors = validate_all(findings, evidence)
        if errors:
            for error in errors:
                print(f"Validation error: {error}", file=sys.stderr)
            return 1
        if args.command == "validate":
            print(f"Validation successful. {len(findings)} finding(s) processed.")
        elif args.command == "report":
            generate_report(findings, args.output, timestamp=args.timestamp, evidence_registry=evidence)
            print(f"Report generated successfully at {args.output}")
        else:
            export_csv(findings, args.output, schema_fields=REQUIRED_FINDING_FIELDS)
            print(f"Exported successfully to {args.output}")
        return 0
    except (ValidationError, ValueError, FileNotFoundError) as exc:
        print(f"Data error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Unexpected programming error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
