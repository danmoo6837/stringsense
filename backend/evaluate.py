"""Evaluate the production note extractor against GuitarSet JAMS annotations."""
import argparse
import csv
import hashlib
import json
import math
import io
import uuid
from urllib.request import Request, urlopen
from urllib.parse import urljoin, urlsplit
import platform
import time
from datetime import datetime, timezone
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path

import numpy as np
import pretty_midi
from mir_eval.transcription import match_notes

ROOT = Path(__file__).resolve().parent


def analyze_via_api(base_url, audio_path, timeout):
    boundary = uuid.uuid4().hex
    body = (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="sample.wav"\r\n'
            'Content-Type: audio/wav\r\n\r\n').encode() + audio_path.read_bytes() + f'\r\n--{boundary}--\r\n'.encode()
    request = Request(base_url.rstrip('/') + '/analyze', data=body,
                      headers={'Content-Type': f'multipart/form-data; boundary={boundary}'})
    with urlopen(request, timeout=timeout) as response:
        result = json.load(response)
    midi_url = urljoin(base_url.rstrip('/') + '/', result['midi_url'])
    if urlsplit(midi_url).netloc != urlsplit(base_url).netloc:
        raise ValueError('MIDI URL must belong to the evaluation server')
    with urlopen(midi_url, timeout=timeout) as response:
        midi_bytes = response.read()
    midi = pretty_midi.PrettyMIDI(io.BytesIO(midi_bytes))
    notes = sorted([dict(start=n.start, end=n.end, pitch=n.pitch)
                    for instrument in midi.instruments if not instrument.is_drum
                    for n in instrument.notes], key=lambda n: n['start'])
    return notes, result, midi_bytes


def read_reference(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    annotations = [a for a in data["annotations"] if a["namespace"] == "note_midi"]
    if not annotations:
        raise ValueError("No note_midi annotations")
    notes = []
    for annotation in annotations:
        for item in annotation["data"]:
            start, duration, pitch = float(item["time"]), float(item["duration"]), float(item["value"])
            if not all(math.isfinite(v) for v in (start, duration, pitch)) or start < 0 or duration <= 0:
                raise ValueError("Invalid reference note")
            notes.append({"start": start, "end": start + duration, "pitch": pitch})
    return sorted(notes, key=lambda n: n["start"])


def metrics(tp, reference, estimated):
    p = tp / estimated if estimated else 0.0
    r = tp / reference if reference else 0.0
    return dict(tp=tp, fp=estimated-tp, fn=reference-tp,
                precision=p, recall=r, f1=2*p*r/(p+r) if p+r else 0.0)


def score(reference, estimated, onset=0.05, cents=50.0, offset_ratio=0.2, offset_min=0.05):
    def arrays(notes):
        intervals = np.array([[n["start"], n["end"]] for n in notes], dtype=float).reshape(-1, 2)
        pitches = 440 * 2 ** ((np.array([n["pitch"] for n in notes], dtype=float) - 69) / 12)
        return intervals, pitches
    ri, rp = arrays(reference)
    ei, ep = arrays(estimated)
    result = {}
    for name, ratio in (("onset_pitch", None), ("onset_pitch_offset", offset_ratio)):
        pairs = match_notes(ri, rp, ei, ep, onset_tolerance=onset,
                            pitch_tolerance=cents, offset_ratio=ratio,
                            offset_min_tolerance=offset_min) if reference and estimated else []
        result[name] = metrics(len(pairs), len(reference), len(estimated))
    return result


def discover(inputs):
    refs = {p.stem: p for p in (inputs / "annotation").glob("*.jams")}
    paths = list((inputs / "audio_mono-mic").rglob("*.wav"))
    audio = {p.stem.removesuffix("_mic"): p for p in paths}
    if len(audio) != len(paths):
        raise ValueError("Duplicate audio names in dataset")
    if not refs or not audio:
        raise ValueError("Expected annotation/*.jams and audio_mono-mic/*.wav")
    if refs.keys() != audio.keys():
        raise ValueError(f"Missing audio: {sorted(refs.keys()-audio.keys())}; missing annotations: {sorted(audio.keys()-refs.keys())}")
    return [(key, refs[key], audio[key]) for key in sorted(refs)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, default=ROOT / "data/inputs")
    parser.add_argument("--output", type=Path, help="New run directory; must not already exist")
    parser.add_argument("--limit", type=int, help="First N sorted tracks (smoke test, not representative)")
    parser.add_argument("--track", help="Exact annotation stem for a single track")
    parser.add_argument("--group", choices=["all", "solo", "comp"], default="all")
    parser.add_argument("--onset-ms", type=float, default=50)
    parser.add_argument("--pitch-cents", type=float, default=50)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--timeout", type=float, default=600, help="Per-request timeout in seconds")
    args = parser.parse_args()
    if (args.limit is not None and args.limit < 1) or not all(math.isfinite(v) and v > 0 for v in (args.onset_ms, args.pitch_cents)):
        parser.error("Limit and tolerances must be positive finite values")
    pairs = discover(args.inputs)
    total = len(pairs)
    if args.group != "all":
        pairs = [p for p in pairs if p[0].endswith("_" + args.group)]
    if args.track:
        pairs = [p for p in pairs if p[0] == args.track]
        if not pairs:
            parser.error("Track not found")
    if args.limit:
        pairs = pairs[:args.limit]
    if args.validate_only:
        count = sum(len(read_reference(p)) for _, p, _ in pairs)
        print(f"Validated {len(pairs)}/{total} pairs, {count} reference notes")
        return 0

    output = args.output or ROOT / "data/evaluations" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output.mkdir(parents=True, exist_ok=False)
    packages = {}
    for package in ("mir_eval", "numpy", "pretty_midi"):
        try:
            packages[package] = version(package)
        except PackageNotFoundError:
            packages[package] = None
    config = dict(started_utc=datetime.now(timezone.utc).isoformat(), inputs=str(args.inputs.resolve()),
                  total_pairs=total, group=args.group, selected=[p[0] for p in pairs], onset_ms=args.onset_ms,
                  pitch_cents=args.pitch_cents, offset_ratio=0.2, offset_min_seconds=0.05,
                  python=platform.python_version(), evaluator_packages=packages,
                  base_url=args.base_url, evaluation_source="POST /analyze -> downloaded MIDI",
                  server_engine="not reported by API", timeout=args.timeout,
                  evaluator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (output / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    completed, errors = [], []
    for index, (key, annotation, audio_path) in enumerate(pairs, 1):
        print(f"[{index}/{len(pairs)}] {key}", flush=True)
        started = time.perf_counter()
        try:
            reference = read_reference(annotation)
            estimated, api_result, midi_bytes = analyze_via_api(args.base_url, audio_path, args.timeout)
            (output / f"{key}.mid").write_bytes(midi_bytes)
            scores = score(reference, estimated, args.onset_ms / 1000, args.pitch_cents)
            record = dict(track=key, group=key.rsplit("_", 1)[-1], engine="server_api",
                          seconds=time.perf_counter()-started, reference_count=len(reference),
                          estimated_count=len(estimated), scores=scores, api_result=api_result,
                          annotation_sha256=hashlib.sha256(annotation.read_bytes()).hexdigest(),
                          audio_sha256=hashlib.sha256(audio_path.read_bytes()).hexdigest())
            completed.append(record)
            (output / f"{key}.json").write_text(json.dumps(dict(**record, reference=reference, estimated=estimated), indent=2), encoding="utf-8")
            print(f"  {record['engine']}: onset+pitch F1={scores['onset_pitch']['f1']:.2%}", flush=True)
        except Exception as exc:
            errors.append(dict(track=key, error=f"{type(exc).__name__}: {exc}"))
            print(f"  ERROR: {exc}", flush=True)
        summary = dict(dataset_pairs=total, selected=len(pairs), completed=len(completed), errors=errors,
                       status="running", score_scale="0..1", aggregates={})
        for group in ("all", "solo", "comp"):
            tracks = [r for r in completed if group == "all" or r["group"] == group]
            summary["aggregates"][group] = {"tracks": len(tracks)}
            for name in ("onset_pitch", "onset_pitch_offset"):
                summary["aggregates"][group][name] = dict(
                    micro=metrics(sum(r["scores"][name]["tp"] for r in tracks), sum(r["reference_count"] for r in tracks), sum(r["estimated_count"] for r in tracks)),
                    macro_f1=sum(r["scores"][name]["f1"] for r in tracks)/len(tracks) if tracks else None)
        (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    summary["status"] = "complete" if not errors else "partial_failure"
    (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    with (output / "tracks.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        fields = ["track", "group", "engine", "seconds", "reference_count", "estimated_count"]
        score_fields = [f"{name}_{metric}" for name in ("onset_pitch", "onset_pitch_offset") for metric in ("precision", "recall", "f1", "tp", "fp", "fn")]
        writer = csv.DictWriter(handle, fieldnames=fields+score_fields)
        writer.writeheader()
        for row in completed:
            writer.writerow({**{k: row[k] for k in fields}, **{f"{name}_{k}": v for name, values in row["scores"].items() for k, v in values.items()}})
    print(f"Results: {output}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
