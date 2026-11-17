"""MusicXML generation and professional PDF engraving with MuseScore."""
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np

DIVISIONS = 4
BAR_TICKS = 16
OPEN_STRINGS = [40, 45, 50, 55, 59, 64]
PITCHES = [("C", 0), ("C", 1), ("D", 0), ("D", 1), ("E", 0),
           ("F", 0), ("F", 1), ("G", 0), ("G", 1), ("A", 0), ("A", 1), ("B", 0)]


def el(parent, tag, text=None, **attributes):
    node = ET.SubElement(parent, tag, attributes)
    if text is not None:
        node.text = str(text)
    return node


def quantize(events, rhythm=None):
    """Map detected beats to a sixteenth-note grid; do not modify raw events."""
    bpm = rhythm["bpm"] if rhythm else 120
    boundaries = list(rhythm["bar_boundaries"]) if rhythm else [0.0]
    duration = max((max(e["end"], e["start"] + .001) for e in events), default=0)
    while len(boundaries) < 2 or boundaries[-1] < duration:
        boundaries.append(boundaries[-1] + 240 / bpm)
    points, ticks = [], []
    for i, (start, end) in enumerate(zip(boundaries, boundaries[1:])):
        inside = [b for b in (rhythm or {}).get("beat_times", []) if start + 1e-5 < b < end - 1e-5]
        times = [start, *inside, end] if len(inside) == 3 else np.linspace(start, end, 5)
        points.extend(times[:-1])
        ticks.extend(i * BAR_TICKS + j * DIVISIONS for j in range(4))
    points.append(boundaries[-1])
    ticks.append((len(boundaries) - 1) * BAR_TICKS)
    result = []
    for e in events:
        start = max(0, int(np.floor(np.interp(e["start"], points, ticks) + .5)))
        end = max(start + 1, int(np.floor(np.interp(e["end"], points, ticks) + .5)))
        pitch = int(e.get("pitch", OPEN_STRINGS[e["string"]] + e["fret"]))
        result.append({**e, "pitch": pitch, "tick_start": start, "tick_end": end})
    # A reattack of the same pitch ends the earlier note in this score voice.
    # Quantized unisons share one notehead; raw MIDI is left untouched.
    by_pitch = {}
    for event in sorted(result, key=lambda e: e["tick_start"]):
        previous = by_pitch.get(event["pitch"])
        if previous and previous["tick_end"] > event["tick_start"]:
            previous["tick_end"] = event["tick_start"]
        by_pitch[event["pitch"]] = event
    result = [e for e in result if e["tick_end"] > e["tick_start"]]
    bars = max(len(boundaries) - 1, max(((e["tick_end"] + 15) // 16 for e in result), default=1))
    return result, bars, bpm


def write_voice(measure, events, offset, staff, voice, tab=False):
    end = offset + BAR_TICKS
    relevant = [e for e in events if e["tick_start"] < end and e["tick_end"] > offset]
    cuts = {offset, end}
    for e in relevant:
        cuts.update((max(offset, e["tick_start"]), min(end, e["tick_end"])))
    if relevant:
        cuts.update(range(offset + 4, end, 4))
    cuts = sorted(cuts)
    for a, b in zip(cuts, cuts[1:]):
        active = {e["pitch"]: e for e in relevant if e["tick_start"] <= a < e["tick_end"]}
        cursor = a
        while cursor < b:
            length = max(n for n in (1, 2, 3, 4, 6, 8, 12, 16) if n <= b - cursor)
            for index, event in enumerate(sorted(active.values(), key=lambda e: e["pitch"]) or [None]):
                note = el(measure, "note")
                if index:
                    el(note, "chord")
                if event:
                    pitch = el(note, "pitch")
                    step, alter = PITCHES[event["pitch"] % 12]
                    el(pitch, "step", step)
                    if alter:
                        el(pitch, "alter", alter)
                    # Guitar notation is written one octave above its sound.
                    el(pitch, "octave", event["pitch"] // 12 - (1 if tab else 0))
                else:
                    el(note, "rest")
                el(note, "duration", length)
                ties = []
                if event and event["tick_start"] < cursor:
                    ties.append("stop")
                if event and event["tick_end"] > cursor + length:
                    ties.append("start")
                for tie in ties:
                    el(note, "tie", type=tie)
                el(note, "voice", voice)
                el(note, "type", {1:"16th", 2:"eighth", 3:"eighth", 4:"quarter", 6:"quarter",
                                  8:"half", 12:"half", 16:"whole"}[length])
                if length in (3, 6, 12):
                    el(note, "dot")
                if tab:
                    el(note, "stem", "none")
                el(note, "staff", staff)
                if event:
                    notations = el(note, "notations")
                    for tie in ties:
                        el(notations, "tied", type=tie)
                    if tab:
                        technical = el(notations, "technical")
                        el(technical, "string", 6 - event["string"])
                        el(technical, "fret", event["fret"])
            cursor += length


def to_musicxml(events, output_dir, rhythm=None, title="Stringsense"):
    events, bar_count, bpm = quantize(events, rhythm)
    score = ET.Element("score-partwise", version="4.0")
    el(el(score, "work"), "work-title", title)
    scaling = el(el(score, "defaults"), "scaling")
    el(scaling, "millimeters", 7)
    el(scaling, "tenths", 40)
    parts = el(score, "part-list")
    for pid in ("P1", "P2"):
        part_info = el(parts, "score-part", id=pid)
        el(part_info, "part-name", "", **{"print-object": "no"})
        el(part_info, "part-abbreviation", "", **{"print-object": "no"})
    for pid in ("P1", "P2"):
        tab = pid == "P2"
        part = el(score, "part", id=pid)
        for bar in range(bar_count):
            measure = el(part, "measure", number=str(bar + 1), width="280")
            if bar % 2 == 0:
                el(measure, "print", **{"new-system": "yes" if bar else "no"})
            if bar == 0:
                attributes = el(measure, "attributes")
                el(attributes, "divisions", DIVISIONS)
                time = el(attributes, "time")
                el(time, "beats", 4)
                el(time, "beat-type", 4)
                el(attributes, "staves", 1)
                clefs = ((1, "TAB", 5),) if tab else ((1, "G", 2),)
                for number, sign, line in clefs:
                    clef = el(attributes, "clef", number=str(number))
                    el(clef, "sign", sign)
                    el(clef, "line", line)
                if tab:
                    details = el(attributes, "staff-details")
                    el(details, "staff-lines", 6)
                    for number, pitch in enumerate(OPEN_STRINGS, 1):
                        tuning = el(details, "staff-tuning", line=str(number))
                        el(tuning, "tuning-step", PITCHES[pitch % 12][0])
                        el(tuning, "tuning-octave", pitch // 12 - 1)
                else:
                    transpose = el(attributes, "transpose")
                    el(transpose, "diatonic", 0)
                    el(transpose, "chromatic", 0)
                    el(transpose, "octave-change", -1)
            offset = bar * BAR_TICKS
            if tab:
                write_voice(measure, events, offset, 1, 1, tab=True)
            else:
                write_voice(measure, events, offset, 1, 1)
            if bar == bar_count - 1:
                el(el(measure, "barline", location="right"), "bar-style", "light-heavy")
    path = Path(output_dir) / "result.musicxml"
    ET.indent(score)
    ET.ElementTree(score).write(path, encoding="utf-8", xml_declaration=True)
    return str(path)


def to_pdf(events, output_dir, rhythm=None, title="Stringsense"):
    source = to_musicxml(events, output_dir, rhythm, title)
    executable = os.environ.get("MUSESCORE_BIN") or next(
        (p for name in ("musescore3", "mscore3", "musescore", "mscore", "MuseScore4")
         if (p := shutil.which(name))), None)
    if not executable:
        raise RuntimeError("MuseScore is required for PDF export. Run the Docker backend or set MUSESCORE_BIN.")
    path = Path(output_dir).resolve() / "result_tab.pdf"
    with tempfile.TemporaryDirectory(prefix="stringsense-score-") as profile:
        env = {**os.environ, "QT_QPA_PLATFORM": "offscreen", "XDG_CONFIG_HOME": profile,
               "XDG_RUNTIME_DIR": profile}
        result = subprocess.run([executable, "-s", "-o", str(path), str(Path(source).resolve())],
                                env=env, capture_output=True, text=True, timeout=120)
    Path(output_dir, "engraving.log").write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode or not path.exists() or not path.read_bytes().startswith(b"%PDF-"):
        raise RuntimeError(f"MuseScore PDF export failed; see {output_dir}/engraving.log")
    return str(path)
