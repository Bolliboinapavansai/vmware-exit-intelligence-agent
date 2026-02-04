import argparse
from pathlib import Path
import json
from typing import List
from .utils.log import setup_logging, logger
from .models import VMModel
from .analyzer.classifier import RuleEngine
from .analyzer.scoring import score_vm, risk_level
from .reporter.json_out import write_classification
from .reporter.csv_out import write_summary_csv
from .reporter.md_report import write_markdown_report


def analyze(input_file: Path, rules_file: Path, out_dir: Path) -> None:
    setup_logging()
    logger.info("Loading rules: %s", str(rules_file))
    engine = RuleEngine(rules_file)

    logger.info("Loading inventory: %s", str(input_file))
    data = json.loads(input_file.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit("Input inventory must be a JSON array of VM objects")

    records = []
    for item in data:
        vm = VMModel(**item).model_dump()
        category, confidence, rule_name, classification_reason = engine.classify(vm)
        score, trace = score_vm(vm)
        rl = risk_level(score)

        reasons = [classification_reason]
        reasons.extend(trace)

        out = {
            "vm_id": vm["vm_id"],
            "name": vm["name"],
            "power_state": vm["power_state"],
            "category": category,
            "confidence": confidence,
            "risk_score": score,
            "risk_level": rl,
            "reasons": reasons,
            "trace": trace,
            "tags": vm.get("tags", []),
            "rule_name": rule_name,
        }
        records.append(out)

    write_classification(out_dir, records)
    write_summary_csv(out_dir, records)
    write_markdown_report(out_dir, records)

    logger.info("Wrote outputs to %s", str(out_dir))


def main():
    parser = argparse.ArgumentParser(prog="vmxagent")
    sub = parser.add_subparsers(dest="cmd")

    analyze_p = sub.add_parser("analyze")
    analyze_p.add_argument("--input", required=True, type=Path)
    analyze_p.add_argument("--rules", required=True, type=Path)
    analyze_p.add_argument("--out", required=True, type=Path)

    args = parser.parse_args()
    if args.cmd == "analyze":
        analyze(args.input, args.rules, args.out)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
