# VMware Exit Intelligence Agent — Phase 1 Analysis

- Total VMs analyzed: **4**

## Risk Level Breakdown

- **High**: 0
- **Medium**: 2
- **Low**: 2

## Migration Category Breakdown

- **keep**: 2
- **rehost**: 1
- **retire**: 1

## Top 10 Highest-Risk & Action Items

| vm_id | name | risk | level | category | decision_reason |
|---|---|---:|---|---|---|
| vm-002 | db-high-snap | 55 | Medium | rehost | Complex snapshot state (8 snapshots) requires stateful re... |
| vm-001 | app-legacy-2008 | 35 | Medium | keep | Windows Server 2008 legacy OS requires on-premises infras... |
| vm-003 | legacy-centos6 | 25 | Low | keep | CentOS 6 legacy OS not supported in cloud targets |
| vm-004 | zombie-off | 10 | Low | retire | Powered off for 120 days; requires decommission |

## Retire (Zombie/Decommission) VMs

| vm_id | name | powered_off_days | category | risk_score | action |
|---|---|---:|---|---:|---|
| vm-004 | zombie-off | 120 | retire | 10 | Decommission |

## Rules Applied

This Phase 1 analysis enforces these rules:

1. **Zombie Detection**: VM poweredOff > 60 days → Retire

2. **Legacy OS**: Windows 2008/2003, RHEL 6, CentOS 6 → Keep (on-premises)

3. **Complexity**: Too many snapshots, multi-NIC, tools issues, large disk → Rehost

4. **Refactor Candidate**: Linux + low risk + single NIC + small disk (very conservative)

5. **Default**: Keep on-premises (conservative default)
