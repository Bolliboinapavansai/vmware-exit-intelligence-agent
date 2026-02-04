# VMware Exit Intelligence Agent – Phase 1 (Read-Only)

## Overview

VMware Exit Intelligence Agent is an enterprise-grade, open-source classification tool that analyzes VMware infrastructure and generates conservative recommendations for IT modernization planning. Phase 1 focuses exclusively on **read-only decision intelligence** – analyzing VMs and recommending actions without executing any migrations.

## What This Tool Is

A deterministic rules-based classifier that processes VMware inventory data and assigns each VM to one of four migration categories:

- **keep** – Remain on-premises infrastructure (conservative default)
- **rehost** – Lift-and-shift candidates requiring careful planning
- **retire** – Decommission or deactivate (zombie VMs)
- **refactor_candidate** – Potential containerization candidates (very restrictive criteria)

Each classification includes:
- Migration category
- Confidence level (high, medium, low)
- Human-readable reasoning
- Risk scoring (0-100)
- Complete audit trail (which rule matched, why)

## What Problem It Solves

Organizations planning VMware exits face analysis paralysis:

- Hundreds or thousands of VMs to categorize
- Complex interdependencies (snapshots, networking, tools)
- Legacy OS constraints
- No clear framework for grouping VMs by migration approach

This tool **eliminates subjectivity** by applying transparent, auditable rules that categorize VMs deterministically.

## What Phase 1 DOES

Phase 1 provides **read-only analysis intelligence**:

1. **Classifies VMs** into migration categories based on explicit rules
2. **Scores risk** using objective signals (snapshots, complexity, age)
3. **Identifies zombies** (powered-off VMs incurring cost)
4. **Protects legacy OS** (Windows 2008/2003, RHEL 6, CentOS 6)
5. **Flags complexity** (multi-NIC, stateful workloads)
6. **Defaults conservatively** (unknown VMs stay on-premises)
7. **Produces auditable output** (CSV, JSON, Markdown reports)

All decisions are:
- **Deterministic** – Same input always produces same output
- **Explainable** – Every classification includes reasoning
- **Auditable** – Complete trace of which rules matched
- **Conservative** – Errs toward keeping on-premises when uncertain

## What Phase 1 DOES NOT Do

Phase 1 explicitly does NOT include:

- Migration execution
- Terraform or IaC templates
- Cloud provider integration (AWS, Azure, GCP)
- Security group or network planning
- Cost analysis or cloud pricing
- Change tracking or state management
- Dashboard or visualization
- AI or LLM-based decision making
- Execution recommendations or runbooks

These are intentional scoping decisions. Phase 1 focuses exclusively on analysis so that Phase 2 can safely add planning and execution with proper governance gates.

## How the Rules Work

### Rule Priority (Enforced Order)

Classification rules are evaluated in strict priority order. The first matching rule determines the category. Higher-priority rules cannot be overridden.

```
[Priority 1] ZOMBIE DETECTION (HIGHEST)
  If: Power state = off AND offline > 60 days
  Then: retire (with high confidence)
  Effect: Overrides ALL other rules

[Priority 2] LEGACY OS CONSTRAINT
  If: Guest OS matches (Windows 2008, 2003, RHEL 6, CentOS 6)
  Then: keep (with high confidence)
  Effect: Blocks cloud migration, requires on-premises infrastructure

[Priority 3] COMPLEXITY SIGNALS
  If: Any of (snapshots > 5, nics > 3, tools offline, disk > 300 GB)
  Then: rehost (with high or medium confidence)
  Effect: Requires careful planning; not suitable for aggressive refactoring

[Priority 4] REFACTOR CANDIDATE (VERY CONSERVATIVE)
  If: Linux AND risk_score < 30 AND single NIC AND disk < 100 GB AND no legacy OS
  Then: refactor_candidate (with medium confidence)
  Effect: Only applies to simple, stateless Linux workloads

[Priority 5] DEFAULT CONSERVATIVE (ALWAYS MATCHES)
  If: No higher rule matched
  Then: keep (with medium confidence)
  Effect: Unknown VMs stay on-premises (safest default)
```

### Mandatory Rules (Cannot Be Violated)

These rules have business significance and cannot be bypassed:

**Zombie VM Rule (Priority 1)**

- **Trigger:** VM powered off for > 60 days
- **Category:** retire (mandatory)
- **Confidence:** high
- **Rationale:** Zombie VMs incur cost without providing value; require explicit decommission or reactivation decision. This rule overrides all others.
- **Example:** `vm-004` (Ubuntu, offline 120 days) → retire

**Legacy OS Rule (Priority 2)**

- **Trigger:** Guest OS contains "2008", "2003", "rhel 6", or "centos 6"
- **Category:** keep (mandatory)
- **Confidence:** high
- **Rationale:** Modern cloud targets (AWS, Azure, GCP) don't support legacy OS. Requires on-premises infrastructure.
- **Examples:**
  - `vm-001` (Windows Server 2008) → keep
  - `vm-003` (CentOS 6) → keep

**Complexity Rule (Priority 3)**

- **Triggers:** Any of:
  - Snapshot count > 5
  - Snapshot age > 30 days
  - Network interfaces > 3
  - VMware Tools not running
  - Disk footprint > 300 GB
- **Category:** rehost (mandatory)
- **Confidence:** high (multiple signals) or medium (single signal)
- **Rationale:** Indicates stateful or complex workload; requires careful rehost planning. Not suitable for aggressive refactoring.
- **Example:** `vm-002` (8 snapshots, 4 NICs, 500 GB disk, tools offline) → rehost

### Conservative Defaults

When a VM doesn't match any higher-priority rule:

- **Category:** keep (on-premises)
- **Confidence:** medium
- **Rationale:** Unknown VMs are safer on-premises. This enforces conservative decision-making.

## How to Run

### Prerequisites

```bash
python >= 3.8
pip install pydantic pyyaml rich
```

### Basic Usage

```bash
python -m agent.cli analyze \
  --input examples/sample_inventory.json \
  --rules rules/classification_rules.yaml \
  --out results/
```

### Output Files

- **classification.json** – Detailed per-VM classifications with full decision trail
- **summary.csv** – Compact summary for import into spreadsheets
- **report.md** – Executive markdown report with category breakdown and risk summary

### Sample Inventory Format

```json
[
  {
    "schema_version": 1,
    "vm_id": "vm-001",
    "name": "app-legacy-2008",
    "power_state": "poweredOn",
    "cpu": 4,
    "memory_mb": 8192,
    "disk_gb": 120,
    "guest_os": "Windows Server 2008 R2",
    "tools_status": "running",
    "nics": 2,
    "snapshot_count": 2,
    "max_snapshot_age_days": 10,
    "avg_cpu_usage_pct": 30,
    "avg_mem_usage_pct": 40,
    "uptime_days": 400,
    "tags": ["app:web"]
  }
]
```

## Example Output Explanation

### Sample Run: 4 VMs

```
Input: examples/sample_inventory.json (4 VMs)
Rules: rules/classification_rules.yaml (5 rules, 5 priorities)
Output: classification.json, summary.csv, report.md
```

### Classification Summary

| VM | Scenario | Category | Confidence | Rule | Reason |
|----|----------|----------|------------|------|--------|
| vm-001 | Windows 2008 legacy | keep | high | legacy-os-detection | Legacy OS requires on-premises |
| vm-002 | 8 snapshots, 4 NICs, 500 GB, tools off | rehost | high | workload-complexity | Multiple complexity signals |
| vm-003 | CentOS 6 legacy | keep | high | legacy-os-detection | Legacy OS not cloud-supported |
| vm-004 | Offline 120 days | retire | high | zombie-detection | Powered off > 60 days |

### CSV Output

```csv
vm_id,name,category,confidence,risk_score,risk_level
vm-001,app-legacy-2008,keep,high,35,Medium
vm-002,db-high-snap,rehost,high,55,Medium
vm-003,legacy-centos6,keep,high,25,Low
vm-004,zombie-off,retire,high,10,Low
```

### JSON Output (vm-001 example)

```json
{
  "vm_id": "vm-001",
  "name": "app-legacy-2008",
  "category": "keep",
  "confidence": "high",
  "risk_score": 35,
  "rule_name": "legacy-os-detection",
  "reasons": [
    "Windows Server 2008 legacy OS requires on-premises infrastructure",
    "guest_os_legacy:+25",
    "uptime_days>365:+10"
  ]
}
```

### Markdown Report

```markdown
# VMware Exit Intelligence Agent — Phase 1 Analysis

## Migration Category Breakdown
- keep: 2 (legacy OS)
- rehost: 1 (complexity)
- retire: 1 (zombie)

## Retire (Zombie/Decommission) VMs
vm-004: 120 days offline → Decommission
```

## Why Phase 1 Is Intentionally Conservative

### Conservative by Design

Phase 1 errs on the side of caution:

1. **Unknown VMs default to keep** – No risky default to cloud
2. **Legacy OS always stays on-premises** – Never force incompatible OS to cloud
3. **Complex workloads require careful planning** – Rehost, not refactor
4. **Zombie VMs explicitly surface for decommission** – Prevents accidental cost
5. **Refactor_candidate is very restrictive** – Only simple, Linux VMs qualify

### Why Conservative Matters

- **Risk Reduction:** Limits scope of aggressive modernization initiatives
- **Compliance:** Aligns with regulatory requirements (air-gapped systems, legacy tools)
- **Operational Safety:** Prevents surprise migrations of critical systems
- **Stakeholder Trust:** CIOs and architects can trust Phase 1 decisions
- **Reversibility:** Conservative decisions are easier to second-guess safely

## How Phase 2 Will Extend This Safely

Phase 2 will build execution planning on top of Phase 1's conservative foundation:

### Planned Phase 2 Features

1. **Target Platform Planning**
   - Map each category to specific platforms (on-premises, AWS, Azure, GCP)
   - Generate infrastructure code (Terraform, CloudFormation)
   - Include safety gates: approval workflows, cost estimates, risk assessments

2. **Security & Compliance**
   - Network security group planning
   - Encryption and compliance requirements
   - Regulatory constraint mapping (HIPAA, PCI, SOC 2)

3. **Dependency Analysis**
   - VM interdependencies
   - Application grouping
   - Migration ordering and sequencing

4. **Cost Analysis**
   - On-premises cost (maintenance, power, space)
   - Cloud cost (compute, storage, networking)
   - Total cost of ownership (TCO) comparison

5. **Execution Planning**
   - Migration runbooks
   - Cutover scheduling
   - Rollback procedures
   - Communication templates

### Phase 2 Won't Change Phase 1

Phase 1 decisions remain locked. Phase 2 operates under these constraints:

- Never override a `keep` (legacy OS) classification
- Never override a `retire` (zombie) classification
- Always respect `rehost` complexity signals
- Apply conservative defaults from Phase 1

This allows Phase 2 to be aggressive in planning and execution while respecting Phase 1's conservative analysis.

## Architecture

```
inputs/
  ├─ sample_inventory.json    (VMware export)
  └─ Other VM inventory sources (Phase 2)

rules/
  └─ classification_rules.yaml (Phase 1 rules - LOCKED)

agent/
  ├─ cli.py                   (Command-line interface)
  ├─ models.py                (Pydantic models)
  ├─ analyzer/
  │   ├─ classifier.py        (Rule engine)
  │   ├─ rules.py             (YAML rule loader)
  │   └─ scoring.py           (Risk scoring)
  └─ reporter/
      ├─ json_out.py          (JSON output)
      ├─ csv_out.py           (CSV output)
      └─ md_report.py         (Markdown report)

tests/
  └─ test_phase1_contract.py  (Unit tests - Phase 1 guarantee)

output/
  ├─ classification.json      (Detailed per-VM)
  ├─ summary.csv              (Spreadsheet-friendly)
  └─ report.md                (Executive summary)
```

## Testing & Verification

Phase 1 includes comprehensive unit tests that guarantee contract compliance:

```bash
pytest tests/test_phase1_contract.py -v
```

Tests verify:

- **Category Vocabulary:** Only {keep, rehost, retire, refactor_candidate} allowed
- **Confidence Enumeration:** Only {high, medium, low} allowed
- **Zombie Rule:** Powered-off VMs > 60 days always → retire
- **Legacy OS Rule:** Legacy OS VMs always → keep
- **Complexity Rule:** Complex workloads always → rehost
- **Conservative Default:** Unknown VMs always → keep
- **Determinism:** Same input always produces same output
- **Read-Only:** No execution code, no migrations

All tests fail if Phase 1 contract is violated.

## Determinism Guarantee

Phase 1 is deterministic:

```
Same VMware Inventory + Same Rules = Same Classification (always)
```

This means:

- Running the tool twice produces identical results
- Results are reproducible and auditable
- Useful for CI/CD pipelines and automated compliance checks
- Safe to cache results for performance

## License

Open source under the MIT License.

## Contributing

Phase 1 is locked for stability. Contributions should:

1. **Not change Phase 1 behavior** – Existing rules are final
2. **Not modify category vocabulary** – {keep, rehost, retire, refactor_candidate} are fixed
3. **Not relax conservative defaults** – Unknown → keep is mandatory
4. **Maintain test coverage** – All Phase 1 tests must pass

Contributions to Phase 2 planning features are welcome and will be reviewed separately.

## FAQ

### Q: Can I change the categories?

No. Phase 1 category vocabulary is locked: {keep, rehost, retire, refactor_candidate}. These are intentional choices for enterprise safety.

### Q: Can I relax the zombie rule?

No. VMs powered off > 60 days MUST be classified as retire. This is a mandatory rule protecting against cost waste.

### Q: Can I change rule priority?

No. Rule priority is locked in the Phase 1 contract. Changing priority would risk violating mandatory constraints.

### Q: Will Phase 1 generate migration plans?

No. Phase 1 is read-only decision intelligence. Migration planning is Phase 2.

### Q: Can Phase 1 execute migrations?

No. Phase 1 produces recommendations only. No Terraform, no cloud APIs, no execution.

### Q: How conservative is Phase 1?

Extremely. By design:
- Unknown VMs stay on-premises
- Legacy OS stays on-premises
- Complex workloads require careful planning
- Refactor candidates are very rare

### Q: What if I disagree with a classification?

Review the reasoning in the JSON output. If the decision is correct per Phase 1 rules, the classification stands. If the input data is wrong, correct the inventory. Phase 1 rules are locked to maintain consistency.

### Q: How do I use this in my environment?

1. Export VMware inventory to JSON format
2. Ensure all required fields are present
3. Run the analyzer with your inventory
4. Review the outputs
5. Share markdown report with stakeholders
6. Use categories to plan Phase 2 execution

### Q: Is Phase 1 ready for production?

Yes. Phase 1 is complete, tested, and locked. The rules are stable and cannot change without major version increment.

## Support

For issues, questions, or contributions:

1. Check the example output in this README
2. Review test cases in `tests/test_phase1_contract.py`
3. Read inline comments in `rules/classification_rules.yaml`
4. Open an issue on GitHub with:
   - Your inventory sample (anonymized)
   - Expected vs. actual classification
   - Which rule you think should apply

## Version

VMware Exit Intelligence Agent – Phase 1 (Read-Only)
Version: 1.0 (LOCKED)
Release Date: February 2026

Phase 1 is complete and stable. No breaking changes are planned.
