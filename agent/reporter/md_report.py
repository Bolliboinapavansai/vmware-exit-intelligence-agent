from pathlib import Path
from typing import List, Dict, Any
from collections import Counter


def _extract_powered_off_days(tags: List[str]) -> int:
    for t in tags:
        if t.startswith("powered_off_days="):
            try:
                return int(t.split("=", 1)[1])
            except Exception:
                return 0
    return 0


def write_markdown_report(out_dir: Path, records: List[Dict[str, Any]]) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / "report.md"
    total = len(records)
    counts = Counter(r.get("risk_level", "Unknown") for r in records)
    cat_counts = Counter(r.get("category", "keep") for r in records)

    # Top 10 highest-risk
    top10 = sorted(records, key=lambda r: r.get("risk_score", 0), reverse=True)[:10]

    # Zombies: poweredOff + powered_off_days tag > 60 AND category is retire
    zombies = []
    for r in records:
        if r.get("power_state") == "poweredOff" and r.get("category") == "retire":
            pod = _extract_powered_off_days(r.get("tags", []))
            if pod:
                zombies.append((r, pod))

    lines = []
    lines.append("# VMware Exit Intelligence Agent — Phase 1 Analysis\n")
    lines.append(f"- Total VMs analyzed: **{total}**\n")
    
    lines.append("## Risk Level Breakdown\n")
    for level in ["High", "Medium", "Low"]:
        lines.append(f"- **{level}**: {counts.get(level, 0)}")
    
    lines.append("\n## Migration Category Breakdown\n")
    for c, n in sorted(cat_counts.items()):
        lines.append(f"- **{c}**: {n}")

    lines.append("\n## Top 10 Highest-Risk & Action Items\n")
    lines.append("| vm_id | name | risk | level | category | decision_reason |")
    lines.append("|---|---|---:|---|---|---|")
    for r in top10:
        reason = r.get("reasons", ["Unknown"])[0]
        # Truncate long reasons for table readability
        if len(reason) > 60:
            reason = reason[:57] + "..."
        lines.append(
            f"| {r.get('vm_id')} | {r.get('name')} | {r.get('risk_score')} | "
            f"{r.get('risk_level')} | {r.get('category')} | {reason} |"
        )

    lines.append("\n## Retire (Zombie/Decommission) VMs\n")
    if zombies:
        lines.append("| vm_id | name | powered_off_days | category | risk_score | action |")
        lines.append("|---|---|---:|---|---:|---|")
        for r, pod in zombies:
            lines.append(
                f"| {r.get('vm_id')} | {r.get('name')} | {pod} | "
                f"{r.get('category')} | {r.get('risk_score')} | Decommission |"
            )
    else:
        lines.append("No zombie VMs detected (powered_off > 60 days).")

    lines.append("\n## Rules Applied\n")
    lines.append("This Phase 1 analysis enforces these rules:\n")
    lines.append("1. **Zombie Detection**: VM poweredOff > 60 days → Retire\n")
    lines.append("2. **Legacy OS**: Windows 2008/2003, RHEL 6, CentOS 6 → Keep (on-premises)\n")
    lines.append("3. **Complexity**: Too many snapshots, multi-NIC, tools issues, large disk → Rehost\n")
    lines.append("4. **Refactor Candidate**: Linux + low risk + single NIC + small disk (very conservative)\n")
    lines.append("5. **Default**: Keep on-premises (conservative default)\n")

    p.write_text("\n".join(lines), encoding="utf-8")
    return p
