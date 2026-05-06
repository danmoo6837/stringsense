import os
import pretty_midi

# 탭 렌더링: 위에서부터 e(5), B(4), G(3), D(2), A(1), E(0)
TAB_STRING_ORDER = [5, 4, 3, 2, 1, 0]
TAB_STRING_LABELS = ["e", "B", "G", "D", "A", "E"]
TAB_RESOLUTION = 0.125  # 초당 컬럼 (0.125s = 8th note at ~120bpm)
TAB_MIN_COLS = 16


def to_midi(note_events: list[dict], output_dir: str) -> str:
    """note_events를 MIDI 파일로 저장하고 경로를 반환한다."""
    midi = pretty_midi.PrettyMIDI(initial_tempo=120)
    guitar = pretty_midi.Instrument(program=25)  # Acoustic Guitar (steel)

    for event in note_events:
        note = pretty_midi.Note(
            velocity=80,
            pitch=event["pitch"],
            start=event["start"],
            end=max(event["end"], event["start"] + 0.05),
        )
        guitar.notes.append(note)

    midi.instruments.append(guitar)
    path = os.path.join(output_dir, "result.mid")
    midi.write(path)
    return path


def to_tab(tab_events: list[dict], output_dir: str) -> str:
    """줄/프렛 정보를 ASCII 탭으로 변환하고 텍스트를 반환한다."""
    if not tab_events:
        return _empty_tab()

    total_duration = tab_events[-1]["end"]
    n_cols = max(int(total_duration / TAB_RESOLUTION) + 4, TAB_MIN_COLS)

    # grid[string_idx][col] = 표시할 문자
    grid = [["-"] * n_cols for _ in range(6)]

    for event in tab_events:
        col = int(event["start"] / TAB_RESOLUTION)
        if col >= n_cols:
            continue
        string_idx = event["string"]
        fret_str = str(event["fret"])
        for k, ch in enumerate(fret_str):
            if col + k < n_cols:
                grid[string_idx][col + k] = ch

    lines = []
    for label, string_idx in zip(TAB_STRING_LABELS, TAB_STRING_ORDER):
        row = "".join(grid[string_idx])
        lines.append(f"{label}|{row}|")

    tab_text = "\n".join(lines)

    path = os.path.join(output_dir, "result_tab.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(tab_text)

    return tab_text


def _empty_tab() -> str:
    lines = [f"{label}|----------------|" for label in TAB_STRING_LABELS]
    return "\n".join(lines)
