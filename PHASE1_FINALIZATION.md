# VMware Exit Intelligence Agent — Phase 1

![License](https://img.shields.io/github/license/Bolliboinapavansai/vmware-exit-intelligence-agent)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Tests](https://github.com/Bolliboinapavansai/vmware-exit-intelligence-agent/actions/workflows/tests.yml/badge.svg)
![Phase](https://img.shields.io/badge/phase-1%20locked-green)
![Mode](https://img.shields.io/badge/mode-read--only-success)

### Read-Only Decision Intelligence

Overview

VMware Exit Intelligence Agent is an open-source, read-only analysis tool designed to help organizations assess migration readiness when planning an exit from VMware.

Phase 1 focuses exclusively on decision intelligence, not execution.
It analyzes VM inventory data, identifies risk and operational complexity, and produces conservative, explainable recommendations to help teams determine where to start safely.

This phase is intentionally limited, deterministic, and audit-friendly.

What Problem This Solves

Organizations planning a VMware exit often encounter:

Incomplete or outdated VM inventories

Legacy operating systems blocking cloud migration

Snapshot sprawl and operational instability

Zombie VMs consuming unnecessary cost

Unclear workload prioritization

Pressure to modernize without sufficient context

Phase 1 addresses these challenges by establishing a trusted baseline before any migration, modernization, or automation activities begin.

Phase 1 Contract (Read-Only)

Phase 1 of VMware Exit Intelligence Agent is intentionally constrained.

Phase 1 DOES

Analyze VM inventory data provided as JSON

Calculate deterministic risk scores

Apply conservative, rule-based classification

Identify zombie workloads safe for retirement

Flag legacy operating system constraints

Produce explainable and auditable outputs

Phase 1 DOES NOT

Execute migrations or cutovers

Modify infrastructure or systems

Generate Terraform or other IaC

Recommend cloud providers or targets

Perform dependency discovery

Perform cost modeling

Use AI or LLM-based inference

Provide dashboards or automation

Phase 1 behavior, rules, and outputs are locked and enforced by unit tests.

Classification Categories (Locked)

Phase 1 uses a fixed and enforced category vocabulary:

keep — Constrained or unknown workloads that should remain on-premises

rehost — Stateful or complex workloads suitable for lift-and-shift

retire — Zombie or unused workloads safe to decommission

refactor_candidate — Rare, low-risk Linux workloads suitable for modernization

No additional categories are permitted.

Rule Priority (Deterministic Order)

Rules are evaluated in the following strict order:

Zombie Detection
Powered-off workloads for more than 60 days are classified as retire.

Legacy OS Constraint
Windows Server 2008/2003, RHEL 6, and CentOS 6 workloads are classified as keep.

Complexity Signals
Snapshot sprawl, multiple NICs, tools issues, or large disks result in rehost.

Refactor Candidate (Very Conservative)
Only low-risk, simple Linux workloads qualify as refactor_candidate.

Default
Any workload not matched by higher-priority rules defaults to keep.

Rule priority is enforced and validated through unit tests.

Repository Structure

vmware-exit-agent/

agent/

cli.py

models.py

analyzer/

reporter/

rules/

classification_rules.yaml

examples/

sample_inventory.json

tests/

test_phase1_contract.py

README.md

requirements.txt (or pyproject.toml)

Quickstart
1) Clone the repository
git clone <YOUR_REPO_URL>
cd vmware-exit-agent

2) Create and activate a virtual environment

macOS/Linux:

python3 -m venv .venv
source .venv/bin/activate


Windows (PowerShell):

python -m venv .venv
.venv\Scripts\Activate.ps1

3) Install dependencies

If using requirements.txt:

pip install -r requirements.txt


If using pyproject.toml:

pip install .

4) Run Phase 1 analysis using sample data
python -m agent.cli analyze \
  --input examples/sample_inventory.json \
  --rules rules/classification_rules.yaml \
  --out results/

Output Files

After running the command above, you should see:

results/classification.json — per-VM classification, risk, confidence, reasons, and rule trace

results/summary.csv — spreadsheet-friendly summary

results/report.md — executive summary report

Run Against Your Own Inventory

Provide your inventory file in the same schema as the example.

python -m agent.cli analyze \
  --input /path/to/your_inventory.json \
  --rules rules/classification_rules.yaml \
  --out results/

Validate Phase 1 Contract (Unit Tests)

Run all tests:

pytest -v


Run only the Phase 1 contract tests:

pytest tests/test_phase1_contract.py -v


Expected result: all tests pass.

Input Schema Notes

Your inventory JSON should be an array of VM objects and include fields such as:

vm_id, name, power_state

guest_os, cpu, memory_mb, disk_gb

snapshot_count, max_snapshot_age_days

nics, tools_status, uptime_days

avg_cpu_usage_pct, avg_mem_usage_pct

tags

Use examples/sample_inventory.json as the reference format.

Determinism Guarantee

Given the same input data and rules:

output classifications are always identical

rule evaluation order is fixed

no probabilistic or AI-driven logic is used

This guarantees repeatability and auditability.

Why Phase 1 Is Intentionally Conservative

Phase 1 prioritizes risk reduction over speed.

When information is insufficient, workloads default to keep

Modernization recommendations are intentionally rare

Legacy constraints are respected

No assumptions are made about application dependencies

This minimizes migration risk and builds trust with enterprise platform and architecture teams.

Phase 2 (Future Work)

Phase 2 will extend Phase 1 safely with:

dependency and application grouping

target platform planning

Terraform and IaC generation

cost modeling

security and compliance mapping

execution planning with approvals

Phase 1 decisions remain locked and unchanged.

License

MIT License

Contributing

Contributions are welcome under the following conditions:

Phase 1 rules, categories, and behavior must not be changed

All unit tests must pass

New features must target Phase 2 or later

Determinism and read-only guarantees must be preserved

Status

Phase 1 is locked, tested, and ready for open-source publication.