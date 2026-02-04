from typing import Any, Dict, List, Tuple
from pathlib import Path
from .rules import load_rules


def _eval_condition(vm: Dict[str, Any], cond: Dict[str, Any]) -> bool:
    """Evaluate a single condition against a VM."""
    field = cond.get("field")
    op = cond.get("op")
    val = cond.get("value")
    vm_val = vm.get(field)

    if op == "contains":
        return (vm_val or "").lower().find(str(val).lower()) >= 0
    if op == "eq":
        return vm_val == val
    if op == "neq":
        return vm_val != val
    if op == "gt":
        try:
            return float(vm_val) > float(val)
        except Exception:
            return False
    if op == "gte":
        try:
            return float(vm_val) >= float(val)
        except Exception:
            return False
    if op == "lt":
        try:
            return float(vm_val) < float(val)
        except Exception:
            return False
    if op == "lte":
        try:
            return float(vm_val) <= float(val)
        except Exception:
            return False
    if op == "in":
        return vm_val in val
    if op == "not_in":
        return vm_val not in val

    raise ValueError(f"Unknown operator: {op}")


class RuleEngine:
    """Phase 1 Classification Engine - strict enforcement of allowed categories."""

    ALLOWED_CATEGORIES = {"rehost", "refactor_candidate", "retire", "keep"}
    ALLOWED_CONFIDENCES = {"low", "medium", "high"}

    def __init__(self, rules_path: Path):
        self.rules = load_rules(rules_path)
        self._validate_rules()

    def _validate_rules(self) -> None:
        """Ensure all rules conform to Phase 1 contract."""
        for r in self.rules:
            cat = r.get("category", "").lower()
            conf = str(r.get("confidence", "")).lower()
            if cat not in self.ALLOWED_CATEGORIES:
                raise ValueError(
                    f"Rule '{r.get('name')}' has invalid category '{cat}'. "
                    f"Allowed: {self.ALLOWED_CATEGORIES}"
                )
            if conf not in self.ALLOWED_CONFIDENCES:
                raise ValueError(
                    f"Rule '{r.get('name')}' has invalid confidence '{conf}'. "
                    f"Allowed: {self.ALLOWED_CONFIDENCES}"
                )

    def classify(self, vm: Dict[str, Any]) -> Tuple[str, str, str, str]:
        """Return (category, confidence, matched_rule_name, reason).

        Applies rules in Phase 1 priority order:
        1. Zombie detection (poweredOff > 60 days) → retire
        2. Legacy OS detection → keep
        3. Complex/stateful workloads → rehost
        4. Conservative refactor_candidate eligibility
        5. Default → keep
        """
        # Priority 1: Zombie VM detection (poweredOff > 60 days)
        if vm.get("power_state") == "poweredOff":
            powered_off_days = self._extract_powered_off_days(vm.get("tags", []))
            if powered_off_days and powered_off_days > 60:
                return (
                    "retire",
                    "high",
                    "zombie-detection",
                    f"Powered off for {powered_off_days} days; requires decommission",
                )

        # Priority 2: Legacy OS detection
        guest_os = (vm.get("guest_os") or "").lower()
        legacy_patterns = [
            ("2008", "Windows Server 2008 legacy OS requires on-premises infrastructure"),
            ("2003", "Windows Server 2003 legacy OS requires on-premises infrastructure"),
            ("rhel 6", "RHEL 6 legacy OS not supported in cloud targets"),
            ("centos 6", "CentOS 6 legacy OS not supported in cloud targets"),
        ]
        for pattern, reason in legacy_patterns:
            if pattern in guest_os:
                return "keep", "high", "legacy-os-detection", reason

        # Priority 3: Complex/stateful workloads → rehost
        rehost_reasons = []

        # Too many snapshots
        if vm.get("snapshot_count", 0) > 5:
            rehost_reasons.append(
                f"Complex snapshot state ({vm.get('snapshot_count')} snapshots) requires stateful rehost"
            )

        # Multiple NICs
        if vm.get("nics", 0) > 3:
            rehost_reasons.append(
                f"Multi-NIC configuration ({vm.get('nics')} NICs) requires careful networking planning"
            )

        # Tools not running
        if vm.get("tools_status") != "running":
            rehost_reasons.append(
                f"VMware Tools {vm.get('tools_status', 'unknown')} indicates operational complexity"
            )

        # Large/complex disks
        if vm.get("disk_gb", 0) > 300:
            rehost_reasons.append(
                f"Large disk footprint ({vm.get('disk_gb')} GB) suggests stateful workload"
            )

        if rehost_reasons:
            return (
                "rehost",
                "high" if len(rehost_reasons) > 1 else "medium",
                "workload-complexity",
                "; ".join(rehost_reasons),
            )

        # Priority 4: Conservative refactor_candidate eligibility
        # Only Linux + low risk + single NIC + small disk
        is_linux = "linux" in guest_os or any(
            x in guest_os for x in ["rhel", "centos", "ubuntu", "debian"]
        )

        if is_linux and vm.get("nics", 1) <= 1 and vm.get("disk_gb", 0) <= 100:
            # Very conservative: only if truly low risk signals
            risk_signals = 0
            if vm.get("snapshot_count", 0) > 0:
                risk_signals += 1
            if vm.get("avg_cpu_usage_pct", 0) > 70:
                risk_signals += 1
            if vm.get("avg_mem_usage_pct", 0) > 70:
                risk_signals += 1
            if vm.get("uptime_days", 0) > 365:
                risk_signals += 1

            if risk_signals == 0:
                return (
                    "refactor_candidate",
                    "medium",
                    "conservative-refactor",
                    "Linux; low risk profile; single NIC; small disk; eligible for containerization",
                )

        # Priority 5: Default → keep
        return "keep", "medium", "default-conservative", "Conservative default: keep on-premises"

    def _extract_powered_off_days(self, tags: list) -> int:
        """Extract powered_off_days from tags."""
        for t in tags:
            if t.startswith("powered_off_days="):
                try:
                    return int(t.split("=", 1)[1])
                except Exception:
                    return 0
        return 0

