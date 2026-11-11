"""Read existing SBS poses without editing the SBS domain; emit light-only before/after QA jobs."""
import argparse
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
BAD_POSES = {"810896133189484", "339463879238809", "962702164479831", "182011943700132",
             "326454015490067", "1406533339711789"}
SUNSETS = {"1406533339711789", "223210302566110", "309664504075286", "381800493259507",
           "2279538078845158", "837235577143499", "275528677534382", "3678296072299092"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("before", "after"))
    args = parser.parse_args()
    refs = json.loads((ROOT / "Data/Regions/bialystok-industrial-c/sbs_references.json").read_text(encoding="utf-8-sig"))["references"]
    groups = defaultdict(list)
    for ref in refs:
        groups[ref["width"], ref["height"]].append(ref)
    jobs = []
    for tier in ("Low", "High"):
        for lighting in ("clear", "overcast"):
            for (width, height), group in sorted(groups.items()):
                job = dict(scene="WorldC_High" if tier == "High" else "WorldC", tier=tier,
                           lighting=lighting, width=1280, height=round(1280*height/width),
                           cameras=",".join(r["camera"] for r in group),
                           output=f"artifacts/light-r1/sbs/{args.phase}/renders/{tier}-{lighting}/{width}x{height}",
                           rq="")
                if args.phase == "before":
                    job.update(rq="rq_clearcover=0" + (",rq_fsrsharp=0" if tier == "High" else ""),
                               overrideWhiteClip=True, whiteClip=1.2, shadowFilter=1)
                jobs.append(job)
    (OUT / f"sbs-{args.phase}.json").write_text(json.dumps({"jobs": jobs}, indent=2), encoding="utf-8")
    eligibility = []
    for ref in refs:
        photo_id = ref["source_id"]
        eligibility.append(dict(camera=ref["camera"], source_id=photo_id,
                                photometric_use=photo_id not in BAD_POSES | SUNSETS,
                                rejected_pose_in_s10_review=photo_id in BAD_POSES,
                                sunset_photo=photo_id in SUNSETS,
                                full_frame_photometry=False,
                                note="Use sky/road ROIs, never the full frame (car hoods); poses remain WORKING_VALUE."))
    (OUT / "sbs-light-eligibility.json").write_text(json.dumps(eligibility, indent=2), encoding="utf-8")
    print(f"{args.phase}: {len(jobs)} jobs, {len(refs)*4} renders, "
          f"{sum(r['photometric_use'] for r in eligibility)} daytime photo poses admitted for ROI comparison (WORKING_VALUE)")


if __name__ == "__main__":
    main()
