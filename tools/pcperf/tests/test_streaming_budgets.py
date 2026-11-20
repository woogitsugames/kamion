"""Contract between the PC budget inventory and runtime streaming policy (ADR 0309)."""
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
BUDGET = ROOT / "tools/pcperf/budgets/pc-budgets.json"
POLICY = ROOT / "game/Assets/_Project/World/Runtime/Streaming/StreamingPolicy.cs"
TIERS = ("Low", "Medium", "High", "Ultra")


def test_streaming_world_budget_ladder_and_owner_values():
    inventory = json.loads(BUDGET.read_text(encoding="utf-8"))["streamingWorldMemory"]
    assert inventory["status"] == "WORKING_VALUE"
    budgets = inventory["perTierMB"]
    assert set(budgets) == set(TIERS)
    values = [budgets[tier] for tier in TIERS]
    assert all(value > 0 for value in values)
    assert values == sorted(values), "Low <= Medium <= High <= Ultra"
    assert budgets["Low"] == 850  # D89, retained by ADR 0309
    assert budgets["High"] == budgets["Ultra"] == 2000
    assert budgets["Medium"] == budgets["Low"]  # same Low content envelope


def test_streaming_inventory_matches_desktop_runtime():
    # Static contract for a checkout where Unity must not run. EditMode covers execution.
    source = POLICY.read_text(encoding="utf-8")
    desktop = re.search(r"if \(desktop\)\s*\{\s*switch \(tier\)\s*\{([^}]+)\}", source)
    assert desktop, "desktop tier table must be found; update this contract if its structure changes"
    runtime = {tier: float(value) for tier, value in re.findall(
        r'case "(\w+)": return (\d+(?:\.\d+)?)f;', desktop[1])}
    budgets = json.loads(BUDGET.read_text(encoding="utf-8"))["streamingWorldMemory"]["perTierMB"]
    assert runtime == budgets
    fallback = re.search(r"default: return (\d+(?:\.\d+)?)f;", desktop[1])
    assert fallback and float(fallback[1]) == budgets["Low"]
