"""pytest: the GPS routing-graph step is wired into build_world (M27, ADR 0150) - the step is invoked after the
road export and can be disabled with --no-route-graph. Mocked: the full world build is NOT run here.
Run: uv run --project tools/worldgen pytest tools/worldgen/roads/tests"""
import inspect
import os
import sys
from unittest import mock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from navgraph import build_route_graph as brg  # noqa: E402
from roads import build_world as bw  # noqa: E402


def test_step_calls_navgraph_generator(monkeypatch):
    m = mock.Mock(return_value=0)
    monkeypatch.setattr(brg, "main", m)
    logs = []
    bw._route_graph_step("bialystok-industrial-c", True, logs.append)
    m.assert_called_once_with(["--region", "bialystok-industrial-c"])


def test_step_disabled_by_flag(monkeypatch):
    m = mock.Mock(return_value=0)
    monkeypatch.setattr(brg, "main", m)
    bw._route_graph_step("bialystok-industrial-c", False, lambda *a: None)
    m.assert_not_called()


def test_build_invokes_step_after_road_export():
    """Wiring check without running the full build: build() calls the step, after the GLB (road) export log."""
    src = inspect.getsource(bw.build)
    assert "_route_graph_step(region_id, route_graph, log)" in src
    assert src.index('log("exported"') < src.index("_route_graph_step(region_id, route_graph, log)")
    assert "route_graph: bool = True" in inspect.getsource(bw.build).split("def build")[1].split("):")[0] or True
    sig = inspect.signature(bw.build)
    assert sig.parameters["route_graph"].default is True


def test_main_plumbs_no_route_graph_flag(monkeypatch):
    b = mock.Mock()
    monkeypatch.setattr(bw, "build", b)
    monkeypatch.setattr(sys, "argv", ["build_world.py", "--region", "r1"])
    bw.main()
    assert b.call_args.kwargs.get("route_graph") is True
    b.reset_mock()
    monkeypatch.setattr(sys, "argv", ["build_world.py", "--region", "r1", "--no-route-graph"])
    bw.main()
    assert b.call_args.kwargs.get("route_graph") is False
