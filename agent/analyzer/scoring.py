from typing import List, Tuple


def score_vm(vm: dict) -> Tuple[int, List[str]]:
    """Compute additive risk score (0-100) and return trace list of signals.

    Signals and weights (additive, cap 100):
    - snapshot_count > 5: +20
    - max_snapshot_age_days > 30: +15
    - guest_os contains legacy identifiers: +25
    - tools_status != running: +10
    - nics > 3: +10
    - avg_cpu_usage_pct > 80 OR avg_mem_usage_pct > 80: +15
    - uptime_days > 365: +10
    """
    score = 0
    trace: List[str] = []

    if vm.get("snapshot_count", 0) > 5:
        score += 20
        trace.append("snapshot_count>5:+20")

    if vm.get("max_snapshot_age_days", 0) > 30:
        score += 15
        trace.append("max_snapshot_age_days>30:+15")

    guest = (vm.get("guest_os") or "").lower()
    legacy_tokens = ["2008", "2003", "rhel 6", "centos 6"]
    if any(tok in guest for tok in legacy_tokens):
        score += 25
        trace.append("guest_os_legacy:+25")

    if vm.get("tools_status") != "running":
        score += 10
        trace.append("tools_status_not_running:+10")

    if vm.get("nics", 0) > 3:
        score += 10
        trace.append("nics>3:+10")

    if (vm.get("avg_cpu_usage_pct", 0) > 80) or (vm.get("avg_mem_usage_pct", 0) > 80):
        score += 15
        trace.append("high_avg_usage:+15")

    if vm.get("uptime_days", 0) > 365:
        score += 10
        trace.append("uptime_days>365:+10")

    if score > 100:
        score = 100
    if score < 0:
        score = 0

    return int(score), trace


def risk_level(score: int) -> str:
    if score <= 29:
        return "Low"
    if score <= 69:
        return "Medium"
    return "High"
