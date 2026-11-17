"""Estimate beat timing; meter remains an explicit 4/4 assumption."""
import numpy as np
import librosa


def analyze(audio, sr: int) -> dict:
    duration = len(audio) / sr
    envelope = librosa.onset.onset_strength(y=audio, sr=sr, hop_length=512)
    tempo, frames = librosa.beat.beat_track(
        onset_envelope=envelope, sr=sr, hop_length=512, trim=False,
    )
    beats = librosa.frames_to_time(frames, sr=sr, hop_length=512)
    reliable = len(beats) >= 4 and np.max(envelope, initial=0) > 0
    bpm = float(np.asarray(tempo).reshape(-1)[0]) if reliable else 120.0
    if not np.isfinite(bpm) or bpm <= 0:
        bpm, reliable = 120.0, False
    period = 60.0 / bpm
    if reliable:
        # Beat tracking does not identify the downbeat. Anchor the grid at the
        # tracked beat nearest the first audible attack, then extend backwards.
        attacks = librosa.onset.onset_detect(onset_envelope=envelope, sr=sr,
                                             hop_length=512, units="time")
        first = float(attacks[0]) if len(attacks) else float(beats[0])
        anchor = int(np.argmin(np.abs(beats - first)))
        grid = beats[anchor:].tolist()
        while grid[0] > period:
            grid.insert(0, grid[0] - period)
    else:
        grid = [0.0]
    while grid[-1] < duration or (len(grid) - 1) % 4:
        grid.append(grid[-1] + period)
    if len(grid) == 1:
        grid.extend(period * i for i in range(1, 5))
    # Include a possible pickup before the first tracked beat.
    boundaries = grid[::4]
    if boundaries[0] <= period * .25:
        boundaries[0] = 0.0
    elif boundaries[0] > 1e-6:
        boundaries.insert(0, 0.0)
    return {"bpm": bpm, "time_signature": "4/4", "beats_per_bar": 4,
            "meter_assumed": True, "downbeat_assumed": True,
            "tempo_source": "estimated" if reliable else "fallback",
            "beat_times": grid, "bar_boundaries": boundaries}
