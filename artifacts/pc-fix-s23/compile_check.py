"""Compile check without the Unity editor: runs Unity's bundled Roslyn (csc.dll) on the worktree sources of the
Game.* assemblies, using the response files the editor wrote for the MAIN checkout (references, defines, options).
Read-only for the main checkout: outputs go to the scratchpad. Usage: python compile_check.py <worktree> [asm ...]"""
import glob, os, subprocess, sys

MAIN = r"C:/Users/matma/Documents/Claude/kamion/game"
DAG = "Library/Bee/artifacts/" + os.environ.get("DAG", "1300b0aE.dag")
UNITY = r"C:/Program Files/Unity/Hub/Editor/6000.3.28f1/Editor/Data"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "csc_out_" + os.environ.get("DAG", "1300b0aE.dag") + os.environ.get("WIN", "")).replace("\\", "/")

# assembly -> source dir (relative to game/), in dependency order
ASM = [
    ("Game.Core", "Assets/_Project/Core"),
    ("Game.Platform", "Assets/_Project/Platform"),
    ("Game.Telemetry", "Assets/_Project/Telemetry"),
    ("Game.Rendering", "Assets/_Project/Rendering"),
    ("Game.Vehicle.Physics", "Assets/_Project/Vehicle/Physics"),
    ("Game.Vehicle.Runtime", "Assets/_Project/Vehicle/Runtime"),
    ("Game.Controls", "Assets/_Project/Input"),
    ("Game.Cameras", "Assets/_Project/Camera"),
    ("Game.Audio", "Assets/_Project/Audio"),
    ("Game.World", "Assets/_Project/World/Runtime"),
    ("Game.UI", "Assets/_Project/UI"),
    ("Game.Gameplay", "Assets/_Project/Gameplay"),
    ("Game.Rendering.Editor", "Assets/_Project/Rendering/Editor"),
    ("Game.Editor", "Assets/_Project/Editor"),
    ("Game.Tests.PlayMode", "Assets/_Project/Tests/PlayMode"),
    ("Game.Tests.EditMode", "Assets/_Project/Tests/EditMode"),
]


def sources(game, rel):
    root = os.path.join(game, rel)
    nested = [os.path.dirname(p) for p in glob.glob(os.path.join(root, "**", "*.asmdef"), recursive=True)
              if os.path.normpath(os.path.dirname(p)) != os.path.normpath(root)]
    out = []
    for p in glob.glob(os.path.join(root, "**", "*.cs"), recursive=True):
        if any(os.path.normpath(p).startswith(os.path.normpath(n) + os.sep) for n in nested):
            continue
        out.append(p.replace("\\", "/"))
    return sorted(out)


def main():
    wt = sys.argv[1].replace("\\", "/")
    game = wt + "/game"
    only = set(sys.argv[2:])
    os.makedirs(OUT, exist_ok=True)
    built = set()
    failed = []
    for name, rel in ASM:
        rsp = os.path.join(MAIN, DAG, name + ".rsp")
        if not os.path.exists(rsp):
            print("== %s: no rsp in this configuration (skipped)" % name)
            continue
        lines = open(rsp, encoding="utf-8-sig").read().splitlines()
        new = []
        for ln in lines:
            s = ln.strip()
            if s.startswith('"Assets/') and s.endswith('.cs"'):
                continue  # replaced by the worktree sources
            if s.startswith("-out:"):
                s = '-out:"%s/%s.dll"' % (OUT, name)
            elif s.startswith("-refout:"):
                s = '-refout:"%s/%s.ref.dll"' % (OUT, name)
            elif s.startswith("/additionalfile:") or s.startswith("-analyzer:"):
                continue  # Unity source generators are not needed for a type check of these assemblies
            elif s.startswith('-r:"' + DAG + "/Game."):
                asm = s[len('-r:"' + DAG + "/"):-len('.ref.dll"')]
                if asm in built:
                    s = '-r:"%s/%s.ref.dll"' % (OUT, asm)
                else:
                    s = '-r:"%s/%s/%s.ref.dll"' % (MAIN, DAG, asm)
            elif s.startswith('-r:"Library/'):
                s = '-r:"%s/%s' % (MAIN, s[len('-r:"'):])
            if os.environ.get("WIN") and s == "-define:UNITY_ANDROID":
                new += ["-define:UNITY_STANDALONE", "-define:UNITY_STANDALONE_WIN"]
                continue
            new.append(s)
        src = sources(game, rel)
        new += ['"%s"' % p for p in src]
        if only and name not in only:
            # still needs to be built once so dependants see the worktree API
            pass
        path = os.path.join(OUT, name + ".rsp")
        open(path, "w", encoding="utf-8").write("\n".join(new) + "\n")
        r = subprocess.run([UNITY + "/NetCoreRuntime/dotnet.exe", UNITY + "/DotNetSdkRoslyn/csc.dll", "@" + path],
                           capture_output=True, text=True, cwd=OUT)
        text = (r.stdout + r.stderr)
        errs = [l for l in text.splitlines() if ": error " in l]
        warns = [l for l in text.splitlines() if ": warning " in l]
        print("== %s: %d files, exit %d, %d errors, %d warnings" % (name, len(src), r.returncode, len(errs), len(warns)))
        for l in errs[:40]:
            print("   " + l.replace(game + "/", ""))
        if only and name in only or not only:
            for l in warns:
                if "pc-fix" in l or any(k in l for k in ("MenuInputGate", "PcAutoTier", "PcTierChoice", "DriverInputMixer", "PcSettingsRuntime",
                                                         "InputBindingsPanel", "UiFocus", "HidWheelDriverInput", "QualityTiers")):
                    print("   W " + l.replace(game + "/", ""))
        if r.returncode == 0:
            built.add(name)
        else:
            failed.append(name)
            if not errs:
                print(text[:3000])
    print("FAILED:", failed if failed else "none")


main()
