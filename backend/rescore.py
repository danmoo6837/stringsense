"""Re-score saved actual API predictions without repeating transcription."""
import argparse
import csv
import json
from pathlib import Path
from evaluate import score, metrics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--fixed-both", action="store_true", help="Use identical fixed onset and offset tolerances")
    args = parser.parse_args()
    original = json.loads((args.run / "summary.json").read_text(encoding="utf-8"))
    records = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(args.run.glob("*.json"))]
    records = [r for r in records if "reference" in r and "estimated" in r]
    if len(records) != original["completed"] or not records:
        raise ValueError("Saved track count does not match summary")
    rows, summaries = [], {}
    for ms in (50, 100, 200):
        results = [score(r["reference"], r["estimated"], ms / 1000, 50,
                         offset_ratio=0.0 if args.fixed_both else 0.2,
                         offset_min=ms / 1000 if args.fixed_both else 0.05) for r in records]
        summaries[str(ms)] = {}
        for name in ("onset_pitch", "onset_pitch_offset"):
            total = metrics(sum(s[name]["tp"] for s in results),
                            sum(len(r["reference"]) for r in records),
                            sum(len(r["estimated"]) for r in records))
            summaries[str(ms)][name] = dict(micro=total, macro_f1=sum(s[name]["f1"] for s in results)/len(records))
        if ms == 50 and not args.fixed_both:
            for name in summaries[str(ms)]:
                if summaries[str(ms)][name]["micro"] != original["aggregates"]["all"][name]["micro"]:
                    raise ValueError("50ms baseline does not reproduce")
        for r, s in zip(records, results):
            for name, values in s.items():
                rows.append(dict(track=r["track"], onset_ms=ms,
                                 offset_ms=ms if args.fixed_both else "max(50ms,20% duration)", metric=name, **values))
    output = dict(source_run=str(args.run), tracks=len(records), pitch_cents=50,
                  offset_ratio=0.0 if args.fixed_both else 0.2,
                  offset_rule="same fixed ms as onset" if args.fixed_both else "max(50ms,20% duration)", score_scale="0..1",
                  method="Rescore saved actual API MIDI note events; no new transcription", results=summaries)
    prefix = "onset_offset_tolerance" if args.fixed_both else "onset_tolerance"
    with (args.run / f"{prefix}_tracks.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (args.run / f"{prefix}_summary.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
