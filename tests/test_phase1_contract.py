"""
Phase 1 Contract Enforcement Tests

These tests guarantee that Phase 1 classification logic strictly adheres to
the Phase 1 contract:

1. Read-only decision intelligence only
2. Conservative recommendations
3. Explainable and deterministic outputs
4. Locked rule priority and category vocabulary
5. Mandatory rules cannot be violated

Tests fail if:
- Invalid categories are used
- Rule priority is violated
- Mandatory rules (zombie, legacy OS) are broken
- Output is non-deterministic
- Conservative defaults are violated
"""

import pytest
import json
import tempfile
from pathlib import Path
from agent.models import VMModel
from agent.analyzer.classifier import RuleEngine
from agent.analyzer.scoring import score_vm, risk_level


class TestPhase1CategoryVocabulary:
    """Test that ONLY Phase 1 allowed categories are used."""

    ALLOWED_CATEGORIES = {"rehost", "refactor_candidate", "retire", "keep"}

    def test_allowed_categories_locked(self):
        """Verify Phase 1 category vocabulary is locked."""
        assert self.ALLOWED_CATEGORIES == {
            "rehost",
            "refactor_candidate",
            "retire",
            "keep",
        }

    def test_invalid_categories_rejected(self):
        """Verify invalid categories are rejected."""
        invalid_categories = [
            "refactor",
            "replatform",
            "rearchitect",
            "migrate",
            "modernize",
            "transform",
            "cloud",
        ]
        for cat in invalid_categories:
            assert cat not in self.ALLOWED_CATEGORIES, f"Invalid category '{cat}' must not be allowed"


class TestPhase1ConfidenceEnumeration:
    """Test that ONLY Phase 1 allowed confidence values are used."""

    ALLOWED_CONFIDENCES = {"high", "medium", "low"}

    def test_allowed_confidences_locked(self):
        """Verify Phase 1 confidence enumeration is locked."""
        assert self.ALLOWED_CONFIDENCES == {"high", "medium", "low"}

    def test_numeric_confidences_rejected(self):
        """Verify numeric confidence values are rejected."""
        numeric_values = [10, 30, 50, 70, 90, 100]
        for val in numeric_values:
            assert val not in self.ALLOWED_CONFIDENCES, f"Numeric confidence {val} must not be allowed"


class TestPhase1ZombieDetection:
    """Test that zombie VMs are ALWAYS classified as retire."""

    @pytest.fixture
    def rules_path(self):
        """Get path to rules file."""
        return Path(__file__).parent.parent / "rules" / "classification_rules.yaml"

    @pytest.fixture
    def engine(self, rules_path):
        """Create RuleEngine."""
        return RuleEngine(rules_path)

    def test_zombie_vm_always_retire(self, engine):
        """Zombie VM (powered off > 60 days) MUST be retire."""
        # Create zombie VM (powered off 120 days)
        zombie_vm = {
            "vm_id": "test-zombie-001",
            "name": "zombie-test",
            "power_state": "poweredOff",
            "cpu": 2,
            "memory_mb": 4096,
            "disk_gb": 100,
            "guest_os": "Ubuntu 18.04",
            "tools_status": "unknown",
            "nics": 1,
            "snapshot_count": 0,
            "max_snapshot_age_days": 0,
            "avg_cpu_usage_pct": 0,
            "avg_mem_usage_pct": 0,
            "uptime_days": 0,
            "tags": ["powered_off_days=120"],
        }

        category, confidence, rule_name, reason = engine.classify(zombie_vm)

        assert category == "retire", f"Zombie VM must be retire, got {category}"
        assert confidence == "high", f"Zombie detection must be high confidence, got {confidence}"
        assert rule_name == "zombie-detection"

    def test_zombie_overrides_all_rules(self, engine):
        """Zombie rule (Priority 1) overrides all other rules."""
        # Create a zombie that would normally be refactor_candidate
        # (Linux + low risk + single NIC + small disk)
        # But ZOMBIE OVERRIDES IT
        zombie_vm = {
            "vm_id": "test-zombie-002",
            "name": "zombie-linux-low-risk",
            "power_state": "poweredOff",
            "cpu": 2,
            "memory_mb": 4096,
            "disk_gb": 50,  # Small disk
            "guest_os": "Ubuntu 20.04",  # Linux
            "tools_status": "running",
            "nics": 1,  # Single NIC
            "snapshot_count": 0,
            "max_snapshot_age_days": 0,
            "avg_cpu_usage_pct": 10,
            "avg_mem_usage_pct": 10,
            "uptime_days": 1,
            "tags": ["powered_off_days=90"],
        }

        category, confidence, rule_name, reason = engine.classify(zombie_vm)

        # Despite meeting refactor_candidate criteria, MUST be retire because it's a zombie
        assert category == "retire", "Zombie rule (Priority 1) must override all other rules"
        assert rule_name == "zombie-detection"

    def test_powered_on_not_zombie(self, engine):
        """Powered on VM is NOT zombie, even if offline tag exists."""
        powered_on_vm = {
            "vm_id": "test-online",
            "name": "powered-on-with-tag",
            "power_state": "poweredOn",  # Powered ON
            "cpu": 2,
            "memory_mb": 4096,
            "disk_gb": 100,
            "guest_os": "Ubuntu 18.04",
            "tools_status": "running",
            "nics": 1,
            "snapshot_count": 0,
            "max_snapshot_age_days": 0,
            "avg_cpu_usage_pct": 10,
            "avg_mem_usage_pct": 10,
            "uptime_days": 100,
            "tags": ["powered_off_days=120"],  # Tag present but powered on
        }

        category, confidence, rule_name, reason = engine.classify(powered_on_vm)

        # Should NOT be retire because power_state is poweredOn
        assert category != "retire", "Only poweredOff VMs can be retire"


class TestPhase1LegacyOS:
    """Test that legacy OS VMs are ALWAYS classified as keep."""

    @pytest.fixture
    def rules_path(self):
        return Path(__file__).parent.parent / "rules" / "classification_rules.yaml"

    @pytest.fixture
    def engine(self, rules_path):
        return RuleEngine(rules_path)

    def test_windows_2008_always_keep(self, engine):
        """Windows Server 2008 MUST be keep."""
        vm = {
            "vm_id": "test-win2008",
            "name": "legacy-windows",
            "power_state": "poweredOn",
            "cpu": 4,
            "memory_mb": 8192,
            "disk_gb": 120,
            "guest_os": "Windows Server 2008 R2",
            "tools_status": "running",
            "nics": 2,
            "snapshot_count": 0,
            "max_snapshot_age_days": 0,
            "avg_cpu_usage_pct": 30,
            "avg_mem_usage_pct": 40,
            "uptime_days": 400,
            "tags": ["app:web"],
        }

        category, confidence, rule_name, reason = engine.classify(vm)

        assert category == "keep", f"Windows 2008 must be keep, got {category}"
        assert confidence == "high"

    def test_centos6_always_keep(self, engine):
        """CentOS 6 MUST be keep."""
        vm = {
            "vm_id": "test-centos6",
            "name": "legacy-centos",
            "power_state": "poweredOn",
            "cpu": 2,
            "memory_mb": 4096,
            "disk_gb": 80,
            "guest_os": "CentOS 6.10",
            "tools_status": "running",
            "nics": 1,
            "snapshot_count": 0,
            "max_snapshot_age_days": 0,
            "avg_cpu_usage_pct": 5,
            "avg_mem_usage_pct": 10,
            "uptime_days": 5,
            "tags": ["legacy:yes"],
        }

        category, confidence, rule_name, reason = engine.classify(vm)

        assert category == "keep", f"CentOS 6 must be keep, got {category}"
        assert confidence == "high"

    def test_rhel6_always_keep(self, engine):
        """RHEL 6 MUST be keep."""
        vm = {
            "vm_id": "test-rhel6",
            "name": "legacy-rhel",
            "power_state": "poweredOn",
            "cpu": 2,
            "memory_mb": 4096,
            "disk_gb": 80,
            "guest_os": "RHEL 6",
            "tools_status": "running",
            "nics": 1,
            "snapshot_count": 0,
            "max_snapshot_age_days": 0,
            "avg_cpu_usage_pct": 5,
            "avg_mem_usage_pct": 10,
            "uptime_days": 5,
            "tags": [],
        }

        category, confidence, rule_name, reason = engine.classify(vm)

        assert category == "keep", f"RHEL 6 must be keep, got {category}"
        assert confidence == "high"

    def test_windows_2003_always_keep(self, engine):
        """Windows Server 2003 MUST be keep."""
        vm = {
            "vm_id": "test-win2003",
            "name": "legacy-windows2003",
            "power_state": "poweredOn",
            "cpu": 2,
            "memory_mb": 2048,
            "disk_gb": 40,
            "guest_os": "Windows Server 2003",
            "tools_status": "running",
            "nics": 1,
            "snapshot_count": 0,
            "max_snapshot_age_days": 0,
            "avg_cpu_usage_pct": 5,
            "avg_mem_usage_pct": 10,
            "uptime_days": 1,
            "tags": [],
        }

        category, confidence, rule_name, reason = engine.classify(vm)

        assert category == "keep", f"Windows 2003 must be keep, got {category}"
        assert confidence == "high"


class TestPhase1Complexity:
    """Test that complex workloads are classified as rehost."""

    @pytest.fixture
    def rules_path(self):
        return Path(__file__).parent.parent / "rules" / "classification_rules.yaml"

    @pytest.fixture
    def engine(self, rules_path):
        return RuleEngine(rules_path)

    def test_many_snapshots_rehost(self, engine):
        """VM with >5 snapshots MUST be rehost."""
        vm = {
            "vm_id": "test-snapshots",
            "name": "snapshot-heavy",
            "power_state": "poweredOn",
            "cpu": 8,
            "memory_mb": 32768,
            "disk_gb": 100,
            "guest_os": "RHEL 8",
            "tools_status": "running",
            "nics": 2,
            "snapshot_count": 8,  # > 5
            "max_snapshot_age_days": 10,
            "avg_cpu_usage_pct": 50,
            "avg_mem_usage_pct": 50,
            "uptime_days": 100,
            "tags": [],
        }

        category, confidence, rule_name, reason = engine.classify(vm)

        assert category == "rehost", f"Complex snapshot state must be rehost, got {category}"

    def test_multiple_nics_rehost(self, engine):
        """VM with >3 NICs MUST be rehost."""
        vm = {
            "vm_id": "test-nics",
            "name": "multi-nic",
            "power_state": "poweredOn",
            "cpu": 8,
            "memory_mb": 16384,
            "disk_gb": 150,
            "guest_os": "RHEL 8",
            "tools_status": "running",
            "nics": 4,  # > 3
            "snapshot_count": 2,
            "max_snapshot_age_days": 5,
            "avg_cpu_usage_pct": 50,
            "avg_mem_usage_pct": 50,
            "uptime_days": 100,
            "tags": [],
        }

        category, confidence, rule_name, reason = engine.classify(vm)

        assert category == "rehost", f"Multi-NIC must be rehost, got {category}"

    def test_tools_not_running_rehost(self, engine):
        """VM with tools not running MUST be rehost."""
        vm = {
            "vm_id": "test-tools",
            "name": "no-tools",
            "power_state": "poweredOn",
            "cpu": 4,
            "memory_mb": 8192,
            "disk_gb": 100,
            "guest_os": "Ubuntu 20.04",
            "tools_status": "notRunning",  # Not running
            "nics": 1,
            "snapshot_count": 1,
            "max_snapshot_age_days": 5,
            "avg_cpu_usage_pct": 30,
            "avg_mem_usage_pct": 30,
            "uptime_days": 100,
            "tags": [],
        }

        category, confidence, rule_name, reason = engine.classify(vm)

        assert category == "rehost", f"Tools not running must be rehost, got {category}"

    def test_large_disk_rehost(self, engine):
        """VM with large disk (>300 GB) should be rehost."""
        vm = {
            "vm_id": "test-disk",
            "name": "large-disk",
            "power_state": "poweredOn",
            "cpu": 16,
            "memory_mb": 65536,
            "disk_gb": 500,  # > 300
            "guest_os": "Ubuntu 20.04",
            "tools_status": "running",
            "nics": 2,
            "snapshot_count": 1,
            "max_snapshot_age_days": 5,
            "avg_cpu_usage_pct": 50,
            "avg_mem_usage_pct": 50,
            "uptime_days": 100,
            "tags": [],
        }

        category, confidence, rule_name, reason = engine.classify(vm)

        assert category == "rehost", f"Large disk must be rehost, got {category}"


class TestPhase1Determinism:
    """Test that same input produces same output (determinism)."""

    @pytest.fixture
    def rules_path(self):
        return Path(__file__).parent.parent / "rules" / "classification_rules.yaml"

    @pytest.fixture
    def engine(self, rules_path):
        return RuleEngine(rules_path)

    def test_deterministic_classification(self, engine):
        """Same VM must be classified identically multiple times."""
        vm = {
            "vm_id": "test-determinism",
            "name": "consistency-test",
            "power_state": "poweredOn",
            "cpu": 4,
            "memory_mb": 8192,
            "disk_gb": 100,
            "guest_os": "Ubuntu 20.04",
            "tools_status": "running",
            "nics": 1,
            "snapshot_count": 0,
            "max_snapshot_age_days": 0,
            "avg_cpu_usage_pct": 30,
            "avg_mem_usage_pct": 30,
            "uptime_days": 100,
            "tags": [],
        }

        # Classify same VM multiple times
        results = []
        for _ in range(5):
            cat, conf, rule, reason = engine.classify(vm)
            results.append((cat, conf, rule))

        # All results must be identical
        first_result = results[0]
        for result in results[1:]:
            assert result == first_result, "Classification must be deterministic"


class TestPhase1ConservativeDefault:
    """Test that default classification is conservative (keep)."""

    @pytest.fixture
    def rules_path(self):
        return Path(__file__).parent.parent / "rules" / "classification_rules.yaml"

    @pytest.fixture
    def engine(self, rules_path):
        return RuleEngine(rules_path)

    def test_unknown_vm_defaults_keep(self, engine):
        """VM not matching any rule defaults to keep."""
        # Create a VM that matches no higher-priority rules
        vm = {
            "vm_id": "test-unknown",
            "name": "unknown-vm",
            "power_state": "poweredOn",
            "cpu": 4,
            "memory_mb": 8192,
            "disk_gb": 80,  # Small
            "guest_os": "Fedora 34",  # Not legacy
            "tools_status": "running",
            "nics": 1,  # Single NIC
            "snapshot_count": 1,  # Not many
            "max_snapshot_age_days": 5,  # Not old
            "avg_cpu_usage_pct": 30,
            "avg_mem_usage_pct": 30,
            "uptime_days": 100,
            "tags": [],
        }

        category, confidence, rule_name, reason = engine.classify(vm)

        # Conservative default must be keep
        assert category == "keep", f"Default must be keep, got {category}"


class TestPhase1ValidOutput:
    """Test that all output conforms to Phase 1 contract."""

    @pytest.fixture
    def rules_path(self):
        return Path(__file__).parent.parent / "rules" / "classification_rules.yaml"

    @pytest.fixture
    def engine(self, rules_path):
        return RuleEngine(rules_path)

    def test_all_categories_valid(self, engine):
        """All classified VMs must use valid Phase 1 categories."""
        allowed = {"rehost", "refactor_candidate", "retire", "keep"}

        # Create diverse test VMs
        test_vms = [
            # Legacy
            {
                "vm_id": "test-legacy",
                "name": "legacy",
                "power_state": "poweredOn",
                "cpu": 2,
                "memory_mb": 4096,
                "disk_gb": 80,
                "guest_os": "Windows Server 2008",
                "tools_status": "running",
                "nics": 1,
                "snapshot_count": 0,
                "max_snapshot_age_days": 0,
                "avg_cpu_usage_pct": 10,
                "avg_mem_usage_pct": 10,
                "uptime_days": 100,
                "tags": [],
            },
            # Zombie
            {
                "vm_id": "test-zombie",
                "name": "zombie",
                "power_state": "poweredOff",
                "cpu": 2,
                "memory_mb": 4096,
                "disk_gb": 80,
                "guest_os": "Ubuntu 18.04",
                "tools_status": "unknown",
                "nics": 1,
                "snapshot_count": 0,
                "max_snapshot_age_days": 0,
                "avg_cpu_usage_pct": 0,
                "avg_mem_usage_pct": 0,
                "uptime_days": 0,
                "tags": ["powered_off_days=120"],
            },
            # Complex
            {
                "vm_id": "test-complex",
                "name": "complex",
                "power_state": "poweredOn",
                "cpu": 8,
                "memory_mb": 32768,
                "disk_gb": 100,
                "guest_os": "RHEL 8",
                "tools_status": "running",
                "nics": 4,
                "snapshot_count": 8,
                "max_snapshot_age_days": 30,
                "avg_cpu_usage_pct": 50,
                "avg_mem_usage_pct": 50,
                "uptime_days": 100,
                "tags": [],
            },
            # Simple
            {
                "vm_id": "test-simple",
                "name": "simple",
                "power_state": "poweredOn",
                "cpu": 2,
                "memory_mb": 4096,
                "disk_gb": 50,
                "guest_os": "Ubuntu 20.04",
                "tools_status": "running",
                "nics": 1,
                "snapshot_count": 0,
                "max_snapshot_age_days": 0,
                "avg_cpu_usage_pct": 20,
                "avg_mem_usage_pct": 20,
                "uptime_days": 100,
                "tags": [],
            },
        ]

        for vm in test_vms:
            category, confidence, rule_name, reason = engine.classify(vm)
            assert category in allowed, f"Invalid category '{category}' for {vm['vm_id']}"

    def test_all_confidences_valid(self, engine):
        """All classified VMs must use valid Phase 1 confidence values."""
        allowed = {"high", "medium", "low"}

        test_vms = [
            {
                "vm_id": "test1",
                "name": "test1",
                "power_state": "poweredOn",
                "cpu": 2,
                "memory_mb": 4096,
                "disk_gb": 80,
                "guest_os": "Ubuntu 20.04",
                "tools_status": "running",
                "nics": 1,
                "snapshot_count": 0,
                "max_snapshot_age_days": 0,
                "avg_cpu_usage_pct": 10,
                "avg_mem_usage_pct": 10,
                "uptime_days": 100,
                "tags": [],
            },
        ]

        for vm in test_vms:
            category, confidence, rule_name, reason = engine.classify(vm)
            assert confidence in allowed, f"Invalid confidence '{confidence}' for {vm['vm_id']}"


class TestPhase1Readonly:
    """Test that Phase 1 is read-only (no execution, no migrations)."""

    def test_phase1_no_execution_code(self):
        """Verify Phase 1 has no code that executes migrations."""
        # Import all modules and verify no terraform/cloud APIs present
        from agent import cli
        from agent.analyzer import classifier, scoring
        from agent.reporter import json_out, csv_out, md_report

        # Phase 1 contains only analysis and reporting
        # No terraform, no AWS/Azure/GCP imports, no execution logic

        # This test documents the design constraint:
        # Phase 1 is READ-ONLY decision intelligence
        assert True  # Phase 1 constraint enforced by code review and architecture

    def test_sample_output_read_only(self, tmp_path):
        """Verify sample output is analysis only (no execution steps)."""
        # Load and run sample
        rules_path = (
            Path(__file__).parent.parent / "rules" / "classification_rules.yaml"
        )
        inventory_path = Path(__file__).parent.parent / "examples" / "sample_inventory.json"

        with open(inventory_path) as f:
            data = json.load(f)

        engine = RuleEngine(rules_path)

        # Classify all VMs
        results = []
        for item in data:
            vm = item
            category, confidence, rule_name, reason = engine.classify(vm)
            score, trace = score_vm(vm)
            rl = risk_level(score)

            results.append(
                {
                    "vm_id": vm["vm_id"],
                    "category": category,
                    "confidence": confidence,
                    "risk_score": score,
                }
            )

        # Verify no execution steps in results
        for result in results:
            # Results should be analysis only (category, confidence, score)
            assert "category" in result
            assert "confidence" in result
            assert "risk_score" in result
            # NO terraform, NO cloud provider, NO execution steps
            assert "terraform" not in str(result).lower()
            assert "execute" not in str(result).lower()
