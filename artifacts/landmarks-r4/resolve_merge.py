"""Keep main ordering after proving landmarks material helpers are identical."""
import ast
import json
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[2]
name = "tools/worldgen/streetscape/materials.py"
own = subprocess.check_output(["git", "show", f":2:{name}"], cwd=root).decode("utf-8")
main = subprocess.check_output(["git", "show", f":3:{name}"], cwd=root).decode("utf-8")
helpers = ("_underdeck_pier_paint", "_underdeck_pier_weather")
def functions(source):
    return {n.name: ast.dump(n) for n in ast.parse(source).body if isinstance(n, ast.FunctionDef)}
a, b = functions(own), functions(main)
assert all(a[h] == b[h] for h in helpers)
# Main additionally contains the life stream's trailer/tractor material updates.
# Preserve those from main; outside them only additive-block order differs.
lines = lambda s: sorted(line.strip() for line in s.splitlines() if line.strip() and not line.lstrip().startswith(("#", '"trailer_curtain_', '"tractor_paint_')))
assert lines(own) == lines(main)
(root / name).write_text(main, encoding="utf-8", newline="\n")
licenses = root / "docs/LICENSES.md"
text = licenses.read_text(encoding="utf-8")
assert text.count("<<<<<<< HEAD") == 1 and text.count(">>>>>>> main") == 1
text = "\n".join(line for line in text.splitlines() if line not in ("<<<<<<< HEAD", "=======", ">>>>>>> main")) + "\n"
licenses.write_text(text, encoding="utf-8", newline="\n")
(Path(__file__).parent / "merge-resolution.json").write_text(json.dumps(dict(
    main=subprocess.check_output(["git", "rev-parse", "MERGE_HEAD"], cwd=root).decode().strip(),
    materials_helpers_ast_identical=list(helpers), other_material_lines_identical_except_main_life_updates=True,
    licenses="Union of EC attribution and cab attribution; no entry removed"), indent=2), encoding="utf-8")
