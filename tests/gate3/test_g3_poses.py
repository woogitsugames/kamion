"""ADR 0246: the pose list is derived from the photo-pair cameras, never authored by hand; and the Windows-player mode of
scripts/g3-poses.ps1 (-Exe, D73): command line, verdict over the output folder and the Player.log.

    uv run --no-project --with pytest pytest tests/gate3/test_g3_poses.py -q

The last block drives scripts/g3-poses.ps1 itself against a stand-in player (tests/gate3/fake_g3_player.py); it needs
PowerShell 7 (`pwsh` on PATH or KAMION_PWSH) and a POSIX host, and is skipped otherwise. It proves the script's launch /
wait / collect / exit-code path, NOT the game: the real Kamion.exe is exercised only on Windows by the leader.
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("g3_poses", REPO / "scripts" / "g3_poses.py")
gp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gp)

REGION = "bialystok-industrial-c"


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def test_both_copies_are_current_and_identical():
    assert gp.main(["check", "--region", REGION]) == 0
    paths = gp.data_paths(REGION)
    assert paths["data_out"].read_bytes() == paths["resource_out"].read_bytes()


def test_every_pose_equals_its_photo_pair_camera():
    paths = gp.data_paths(REGION)
    doc = load(paths["resource_out"])
    cams = load(paths["cameras"])["cameras"]
    refs = {r["camera"]: r for r in load(paths["references"])["references"]}
    assert doc["schema"] == gp.SCHEMA
    assert doc["count"] == len(doc["poses"]) == len(cams) == 42
    for i, (p, c) in enumerate(zip(doc["poses"], cams)):
        assert p["index"] == i + 1
        assert p["source"]["cameras_index"] == i
        for k in ("id", "segment", "kind", "pos", "look_at", "fov_deg"):
            assert p[k] == c[k], (p["id"], k)
        r = refs[p["id"]]
        assert (p["reference"]["width"], p["reference"]["height"]) == (r["width"], r["height"])
        assert p["out_width"] == 1280
        assert p["out_height"] == round(1280 * r["height"] / r["width"])
    assert doc["inputs"][gp.rel(paths["cameras"])] == gp.sha256(paths["cameras"])


def test_filter_rule_matches_the_game():
    pose = {"index": 7, "id": "sbs-g3-a-1406533339711789"}
    assert gp.matches(pose, "")
    assert gp.matches(pose, "7")
    assert not gp.matches(pose, "8")
    assert gp.matches(pose, "1-9") and gp.matches(pose, "9-1")
    assert not gp.matches(pose, "8-12")
    assert gp.matches(pose, "140653")          # > 3 digits: id substring, not an index
    assert gp.matches(pose, "SBS_G3_A")
    assert not gp.matches(pose, "g3-b")
    assert gp.matches(pose, "3-a")


# ---------------------------------------------------------------- Windows player: command line (g3_poses.win_player_args)

def pairs(args: list[str]) -> dict[str, str]:
    return {args[i]: args[i + 1] for i in range(0, len(args), 2)}


def test_win_args_one_process_for_all_poses():
    a = gp.win_player_args(run_id="20261116-101500-overcast", lighting="overcast", tier="High",
                           out_dir=r"C:\kamion\artifacts\g3-poses\win\20261116-101500\overcast",
                           log_file=r"C:\kamion\artifacts\g3-poses\win\20261116-101500\Player-overcast.log")
    assert len(a) % 2 == 0
    d = pairs(a)
    # Unity player arguments as in ADR 0261 / 0266: windowed, explicit size, own log file.
    assert (d["-screen-fullscreen"], d["-screen-width"], d["-screen-height"]) == ("0", "1600", "900")
    assert d["-logFile"].endswith("Player-overcast.log")
    # Game arguments ("-key value", DefaultPlatformServices.GetLaunchArgument); keys = G3PoseArgs.Key*.
    assert (d["-scene"], d["-tier"], d["-lighting"]) == ("WorldC", "High", "overcast")
    assert (d["-g3pose"], d["-g3pose_run"], d["-g3pose_width"], d["-g3pose_quit"]) == ("1", "20261116-101500-overcast", "1280", "1")
    assert d["-g3pose_dir"].endswith(r"\overcast")
    assert "-g3pose_only" not in d and "-fps" not in d            # all 42 poses, player default frame cap
    assert "-shot" not in d and "-quit_t" not in d                 # DesktopAutoShot is not used: the runner quits itself
    cs = (REPO / "game/Assets/_Project/Gameplay/G3Poses/G3PoseArgs.cs").read_text(encoding="utf-8")
    for k in d:
        if k.startswith("-g3pose"):
            assert f'"{k[1:]}"' in cs, k


def test_win_args_options_and_refusals():
    base = dict(run_id="r-clear", lighting="clear", tier="Low", out_dir="/o/clear", log_file="/o/Player-clear.log")
    d = pairs(gp.win_player_args(**base, only=" 1-3, cm924 ", width=640, fps=30, screen=(1920, 1080), extra=["g3pose_warmup_s=15"]))
    assert (d["-g3pose_only"], d["-g3pose_width"], d["-fps"], d["-tier"]) == ("1-3,cm924", "640", "30", "Low")
    assert (d["-screen-width"], d["-screen-height"], d["-g3pose_warmup_s"]) == ("1920", "1080", "15")
    for bad in (dict(run_id="a b"), dict(run_id="../x"), dict(run_id=""), dict(lighting="dusk"), dict(lighting="over cast"),
                dict(out_dir=""), dict(width=8), dict(extra=["novalue"])):
        with pytest.raises(ValueError):
            gp.win_player_args(**{**base, **bad})


def test_quote_windows():
    assert gp.quote_windows(["-g3pose_dir", r"C:\Users\Jan Kowalski\k\overcast", "-g3pose", "1"]) == \
        r'-g3pose_dir "C:\Users\Jan Kowalski\k\overcast" -g3pose 1'
    with pytest.raises(ValueError):
        gp.quote_windows(['a"b'])


def test_frame_name_matches_the_game_rule():
    assert gp.frame_name({"index": 7, "id": "sbs-g3-a-1406533339711789"}, "overcast") == "07_sbs-g3-a-1406533339711789_overcast.png"
    assert gp.frame_name({"index": 12, "id": "a b/c"}, "") == "12_abc.png"
    assert gp.sanitize_token("../../etc", 64) == "etc"


# ---------------------------------------------------------------- Windows player: verdict (g3_poses.verify_capture)

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
RUN = "t-overcast"


def make_run(tmp_path: Path, n: int = 3, *, skip: set[int] = frozenset(), same: bool = False, extra_log: str = "",
             done: bool = True, manifest: bool = True, failed: int = 0):
    poses = [{"index": i, "id": f"sbs-g3-a-{i}00"} for i in range(1, n + 1)]
    d = tmp_path / "overcast"
    d.mkdir()
    shots, log = [], ["[BOOT] Kamion 0.1.0 dev"]
    for p in poses:
        if p["index"] in skip:
            continue
        name = gp.frame_name(p, "overcast")
        (d / name).write_bytes(PNG + (b"" if same else bytes([p["index"]])))
        shots.append({"index": p["index"], "id": p["id"], "file": name, "status": "OK"})
        log.append(f"[G3POSE] SHOT {p['index']}/{n} id={p['id']} file={name}")
    if manifest:
        (d / "manifest.json").write_text(json.dumps({"schema": gp.CAPTURE_SCHEMA, "run": RUN, "failed": failed, "timeout": 0,
                                                     "errors": [], "shots": shots}), encoding="utf-8")
    if extra_log:
        log.append(extra_log)
    if done:
        log.append(f"[G3POSE] DONE run={RUN} captured={len(shots)} failed={failed} timeout=0 dir=C:\\Users\\Jan Kowalski\\out")
    return d, poses, "\r\n".join(log)


def test_verify_clean_run(tmp_path):
    d, poses, log = make_run(tmp_path)
    v = gp.verify_capture(d, poses, "overcast", log, RUN, exit_code=0)
    assert v["ok"], v["problems"]
    assert (v["planned"], v["pngs"], v["log"]["shots"]) == (3, 3, 3)
    assert v["log"]["done"] == {"captured": 3, "failed": 0, "timeout": 0, "dir": "C:\\Users\\Jan Kowalski\\out"}


def test_verify_missing_png(tmp_path):
    d, poses, log = make_run(tmp_path, skip={2})
    v = gp.verify_capture(d, poses, "overcast", log, RUN)
    assert not v["ok"]
    assert v["missing"] == ["02_sbs-g3-a-200_overcast.png"]


def test_verify_exception_in_log(tmp_path):
    d, poses, log = make_run(tmp_path, extra_log="NullReferenceException: Object reference not set to an instance of an object")
    v = gp.verify_capture(d, poses, "overcast", log, RUN)
    assert not v["ok"] and len(v["log"]["suspiciousLines"]) == 1
    d2, poses2, log2 = make_run(tmp_path / "b" if (tmp_path / "b").mkdir() is None else tmp_path, extra_log="Crash!!!")
    assert not gp.verify_capture(d2, poses2, "overcast", log2, RUN)["ok"]


def test_verify_timeout_no_done_duplicates_and_stale(tmp_path):
    d, poses, log = make_run(tmp_path, done=False)
    v = gp.verify_capture(d, poses, "overcast", log, RUN, timed_out=True)
    assert not v["ok"] and any(p.startswith("TIMEOUT") for p in v["problems"]) and v["log"]["done"] is None
    assert not gp.verify_capture(d, poses, "overcast", log + f"\n[G3POSE] DONE run=other captured=3 failed=0 timeout=0 dir=x", RUN)["ok"]
    good = log + f"\n[G3POSE] DONE run={RUN} captured=3 failed=0 timeout=0 dir=x"
    assert gp.verify_capture(d, poses, "overcast", good, RUN)["ok"]
    assert not gp.verify_capture(d, poses, "overcast", good, RUN, exit_code=1)["ok"]          # player exit code
    assert not gp.verify_capture(d, poses, "overcast", good, "t-clear")["ok"]                 # another run's folder / log
    assert not gp.verify_capture(d, poses + [{"index": 4, "id": "x"}], "overcast", good, RUN)["ok"]   # fewer frames than planned
    (d / "99_stray_overcast.png").write_bytes(PNG + b"z")
    assert gp.verify_capture(d, poses, "overcast", good, RUN)["unexpected"] == ["99_stray_overcast.png"]


def test_verify_duplicates_bad_png_manifest_refused(tmp_path):
    (tmp_path / "a").mkdir(); (tmp_path / "b").mkdir(); (tmp_path / "c").mkdir(); (tmp_path / "e").mkdir()
    d, poses, log = make_run(tmp_path / "a", same=True)
    v = gp.verify_capture(d, poses, "overcast", log, RUN)
    assert not v["ok"] and len(v["duplicateFrames"]) == 2
    d, poses, log = make_run(tmp_path / "b")
    (d / gp.frame_name(poses[0], "overcast")).write_bytes(b"not a png")
    assert gp.verify_capture(d, poses, "overcast", log, RUN)["badPng"] == ["01_sbs-g3-a-100_overcast.png"]
    d, poses, log = make_run(tmp_path / "c", manifest=False)
    assert not gp.verify_capture(d, poses, "overcast", log, RUN)["ok"]
    v = gp.verify_capture(tmp_path / "nowhere", poses, "overcast",
                          f"[G3POSE] REFUSED: not a Development build\n[G3POSE] DONE run={RUN} captured=0 failed=0 timeout=0 dir=-", RUN)
    assert not v["ok"] and v["log"]["refused"] and v["pngs"] == 0
    # A failed frame reported by the game: FAIL line + failed=1, counted once (its exception text is not "suspicious").
    d, poses, log = make_run(tmp_path / "e", skip={3}, failed=1, extra_log="[G3POSE] FAIL 3/3 id=sbs-g3-a-300 reason=IOException: disk full")
    v = gp.verify_capture(d, poses, "overcast", log, RUN)
    assert not v["ok"] and v["log"]["suspiciousLines"] == [] and len(v["log"]["failLines"]) == 1


def test_cli_winargs_and_verify(tmp_path, capsys):
    assert gp.main(["winargs", "--run", "r-overcast", "--lighting", "overcast", "--out-dir", "/o/overcast", "--log", "/o/p.log"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["args"][out["args"].index("-tier") + 1] == "High" and out["line"].startswith("-screen-fullscreen 0 ")
    assert gp.main(["winargs", "--run", "r", "--lighting", "dusk", "--out-dir", "/o", "--log", "/o/p.log"]) == 2
    capsys.readouterr()
    assert gp.main(["verify", "--dir", str(tmp_path), "--log", str(tmp_path / "none.log"), "--run", "r", "--lighting", "overcast"]) == 6
    v = json.loads(capsys.readouterr().out)
    assert v["planned"] == 42 and len(v["missing"]) == 42 and "player log missing" in v["problems"][0]


# ---------------------------------------------------------------- scripts/g3-poses.ps1 -Exe against a stand-in player

PWSH = os.environ.get("KAMION_PWSH") or shutil.which("pwsh")
needs_pwsh = pytest.mark.skipif(not PWSH or os.name == "nt", reason="needs PowerShell 7 (pwsh / KAMION_PWSH) on a POSIX host")


def run_ps(tmp_path: Path, mode: str, *extra: str, exe: bool = True):
    fake = tmp_path / "Kamion.exe"
    if exe:
        fake.write_text("#!" + sys.executable + "\n" + (REPO / "tests/gate3/fake_g3_player.py").read_text(encoding="utf-8"), encoding="utf-8")
        fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
    # UNITY_EDITOR_ROOT: scripts/env.ps1 builds Windows tool paths from it (its C:\ default does not resolve on POSIX).
    env = {**os.environ, "KAMION_ARTIFACTS_DIR": str(tmp_path / "artifacts"), "G3_FAKE_REPO": str(REPO), "G3_FAKE_MODE": mode,
           "UNITY_EDITOR_ROOT": str(tmp_path / "no-unity"), "NO_COLOR": "1"}
    r = subprocess.run([PWSH, "-NoProfile", "-File", str(REPO / "scripts/g3-poses.ps1"), "-Exe", str(fake), "-SkipCompare", *extra],
                       env=env, capture_output=True, text=True, timeout=300)
    roots = sorted((tmp_path / "artifacts/g3-poses/win").glob("*")) if (tmp_path / "artifacts/g3-poses/win").is_dir() else []
    return r, (roots[-1] if roots else None)


@needs_pwsh
def test_ps1_dry_run_needs_no_exe(tmp_path):
    r, root = run_ps(tmp_path, "ok", "-DryRun", exe=False)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "WINDOWS player" in r.stdout and "42/42 poses, tier High" in r.stdout
    assert r.stdout.count("would run [") == 2 and "-lighting overcast" in r.stdout and "-lighting clear" in r.stdout
    assert root is None                                           # a dry run writes nothing
    r, _ = run_ps(tmp_path, "ok", "-DryRun", "-Lighting", "dusk", exe=False)
    assert r.returncode == 2
    r, _ = run_ps(tmp_path, "ok", "-Serial", "X", "-DryRun", exe=False)      # -Exe and -Serial exclude each other
    assert r.returncode != 0 and "Parameter set cannot be resolved" in (r.stdout + r.stderr)
    r, _ = run_ps(tmp_path, "ok", exe=False)                                 # real run without the exe
    assert r.returncode == 2 and "-Exe not found" in r.stdout


@needs_pwsh
def test_ps1_full_run_collects_42_frames_per_lighting(tmp_path):
    r, root = run_ps(tmp_path, "ok")
    assert r.returncode == 0, r.stdout + r.stderr
    res = json.loads((root / "g3poses-result.json").read_text(encoding="utf-8-sig"))
    assert res["valid"] is True and res["platform"] == "windows" and res["tier"] == "High" and res["posesPlanned"] == 42
    assert [x["status"] for x in res["runs"]] == ["DONE", "DONE"]
    for light in ("overcast", "clear"):
        assert len(list((root / light).glob("*.png"))) == 42
        assert (root / light / "manifest.json").is_file() and (root / f"Player-{light}.log").is_file()
    assert (root / "overcast" / "07_sbs-g3-a-1406533339711789_overcast.png").is_file() or \
        any(f.name.startswith("07_") for f in (root / "overcast").glob("*.png"))


@needs_pwsh
@pytest.mark.parametrize("mode,status", [("missing", "INCOMPLETE"), ("exception", "INCOMPLETE"), ("refused", "REFUSED_BY_GAME"), ("hang", "TIMEOUT")])
def test_ps1_exit_6_on_missing_png_exception_refusal_timeout(tmp_path, mode, status):
    r, root = run_ps(tmp_path, mode, "-Only", "1-3", "-Lighting", "overcast", "-TimeoutSeconds", "6")
    assert r.returncode == 6, r.stdout + r.stderr
    res = json.loads((root / "g3poses-result.json").read_text(encoding="utf-8-sig"))
    assert res["valid"] is False and res["runs"][0]["status"] == status and res["runs"][0]["problems"]
    if mode == "hang":
        assert "TIMEOUT" in r.stdout
