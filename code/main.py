#!/usr/bin/env python3
"""
Multi-Domain Support Triage Agent
Handles HackerRank, Claude, and Visa support tickets
Uses Anthropic Claude API for triage + response generation
"""

import os
import sys
import csv
import json
import time
import random
import pathlib
import argparse

import sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from agent import SupportAgent

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT = pathlib.Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
ISSUES_DIR = ROOT / "support_issues"
INPUT_CSV = ISSUES_DIR / "support_issues.csv"
OUTPUT_CSV = ISSUES_DIR / "output.csv"

# ── Output columns required ───────────────────────────────────────────────────
OUTPUT_FIELDS = ["Issue", "Subject", "Company", "status", "product_area", "response", "justification", "request_type"]


def load_tickets(path: pathlib.Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_output(rows: list[dict], path: pathlib.Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n✅  Wrote {len(rows)} rows → {path}")


def main():
    parser = argparse.ArgumentParser(description="Support Triage Agent")
    parser.add_argument("--input", default=str(INPUT_CSV), help="Input CSV path")
    parser.add_argument("--output", default=str(OUTPUT_CSV), help="Output CSV path")
    parser.add_argument("--sample", action="store_true", help="Use sample_support_issues.csv for validation")
    parser.add_argument("--ticket", type=int, default=None, help="Process only ticket N (0-indexed)")
    args = parser.parse_args()

    if args.sample:
        input_path = ISSUES_DIR / "sample_support_issues.csv"
    else:
        input_path = pathlib.Path(args.input)

    output_path = pathlib.Path(args.output)

    # Load corpus and initialise agent
    print("🚀  Initialising Support Triage Agent...")
    agent = SupportAgent(data_dir=DATA_DIR)

    # Load tickets
    tickets = load_tickets(input_path)
    print(f"📋  Loaded {len(tickets)} tickets from {input_path.name}\n")

    if args.ticket is not None:
        tickets = [tickets[args.ticket]]

    results = []
    for i, ticket in enumerate(tickets):
        issue   = ticket.get("Issue", "").strip()
        subject = ticket.get("Subject", "").strip()
        company = ticket.get("Company", "").strip()

        print(f"[{i+1}/{len(tickets)}] Company={company!r:10} | Subject={subject[:55]!r}")

        # Small jitter to avoid rate-limit bursts
        if i > 0:
            time.sleep(random.uniform(0.3, 0.8))

        result = agent.triage(issue=issue, subject=subject, company=company)

        row = {
            "Issue":         issue,
            "Subject":       subject,
            "Company":       company,
            "status":        result["status"],
            "product_area":  result["product_area"],
            "response":      result["response"],
            "justification": result["justification"],
            "request_type":  result["request_type"],
        }
        results.append(row)

        # Pretty-print
        status_icon = "✅" if result["status"] == "replied" else "🔺"
        print(f"   {status_icon} {result['status'].upper()} | area={result['product_area']} | type={result['request_type']}")
        print(f"   💬 {result['response'][:120].strip()}...")
        print()

    write_output(results, output_path)


if __name__ == "__main__":
    main()
