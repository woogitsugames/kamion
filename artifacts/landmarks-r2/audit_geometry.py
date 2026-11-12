"""Compare generated underdeck invariants against this round's fresh baseline."""
import hashlib
import json
from pathlib import Path

out = Path(__file__).resolve().parent
root = out.parents[1]
generated = root / "Data/Regions/bialystok-industrial-c/generated"
baseline = out / "baseline-generated"


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


old_specs = load(baseline / "underdeck.spec.json")
new_specs = load(generated / "landmarks/viaduct_putry_underdeck.spec.json")
assert len(old_specs) == len(new_specs) == 2
old_qa = load(baseline / "streetscape_qa.json")["hero_bridges"]["underdeck"]
new_qa = load(generated / "streetscape_qa.json")["hero_bridges"]["underdeck"]
old_by_chain = {row["chain"]: row for row in old_qa}
new_by_chain = {row["chain"]: row for row in new_qa}
assert old_by_chain.keys() == new_by_chain.keys()
rows = []
for chain in old_by_chain:
    before, after = old_by_chain[chain], new_by_chain[chain]
    assert before["deck_before_sha256"] == before["deck_after_sha256"] == after["deck_before_sha256"] == after["deck_after_sha256"]
    assert after["new_materials"] == [] and after["vegetation_added"] == 0
    rows.append(dict(chain=chain, preserved_deck_sha256=after["deck_after_sha256"],
                     added_net_tris_before=before["added_net_tris"], added_net_tris_after=after["added_net_tris"],
                     delta_net_tris=after["added_net_tris"] - before["added_net_tris"]))
for before, after in zip(old_specs, new_specs):
    assert before["decks"] == after["decks"], "Columns, bearings, alignment and deck must remain unchanged"
    assert after["params"]["stairs_enabled"] is False
    assert after["stairs"] == [[], []]
old_steps = sum(len(flight) for spec in old_specs for flight in spec["stairs"])
new_steps = sum(len(flight) for spec in new_specs for flight in spec["stairs"])
assert old_steps > 0 and new_steps == 0
roads_before, roads_after = baseline / "roads_qa.json", generated / "roads_qa.json"
assert load(roads_before) == load(roads_after), "Road QA changed relative to the fresh baseline"
result = dict(stair_treads_before=old_steps, stair_treads_after=new_steps,
              stair_flights_before=sum(bool(flight) for spec in old_specs for flight in spec["stairs"]),
              all_decks_identical=True, road_qa_identical=True,
              road_qa_sha256_after=hashlib.sha256(roads_after.read_bytes()).hexdigest(), rows=rows,
              scope="Generated deck V/UV/T hashes plus exact deck specs; UV1/COL preservation additionally covered by unit test")
(out / "geometry-audit.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
