import numpy as np
import librosa

GUITAR_MIDI_MIN = 40  # E2
GUITAR_MIDI_MAX = 88  # E6
MIN_NOTE_DURATION = 0.04
MERGE_GAP = 0.08
MERGE_PITCH_TOLERANCE = 0

HOP_LENGTH = 512
LIBROSA_MIN_ONSET_GAP = 0.05
LIBROSA_MAX_NOTE_DURATION = 1.25


def extract_notes(audio: np.ndarray, sr: int, audio_path: str | None = None) -> list[dict]:
    """Extract with Basic Pitch only; unavailable or empty results stay empty."""
    if audio_path:
        return _extract_with_basic_pitch(audio_path)
    return []


def _extract_with_basic_pitch(audio_path: str) -> list[dict]:
    try:
        from basic_pitch.inference import predict
        _, _, raw_notes = predict(audio_path)
    except Exception:
        import logging
        logging.getLogger(__name__).warning("Basic Pitch failed; returning no notes", exc_info=True)
        return []
    notes = []
    for raw_note in raw_notes:
        parsed = _parse_basic_pitch_note(raw_note)
        if parsed is None:
            continue
        start, end, pitch = parsed
        if end - start < 0.06 or not GUITAR_MIDI_MIN <= pitch <= GUITAR_MIDI_MAX:
            continue
        notes.append(dict(start=start, end=end, pitch=pitch))
    notes.sort(key=lambda event: event["start"])
    return _merge_repeated_notes(notes)


def _parse_basic_pitch_note(raw_note) -> tuple[float, float, int] | None:
    try:
        start, end, pitch = float(raw_note[0]), float(raw_note[1]), int(round(raw_note[2]))
    except (TypeError, ValueError, IndexError):
        return None
    if end <= start:
        return None
    return start, end, pitch


def _extract_with_librosa(audio: np.ndarray, sr: int) -> list[dict]:
    onset_times = _detect_onsets(audio, sr)
    if len(onset_times) == 0:
        return []

    onset_times = _dedupe_onsets(onset_times)
    f0, voiced_flag, voiced_prob = _estimate_f0(audio, sr)
    cqt_mag, freqs = _compute_cqt(audio, sr)
    note_events = _build_librosa_note_events(onset_times, f0, voiced_flag, voiced_prob, cqt_mag, freqs, sr)
    return note_events  # Distinct attacks must retain repeated notes of the same pitch.


def _detect_onsets(audio: np.ndarray, sr: int) -> np.ndarray:
    onset_frames = librosa.onset.onset_detect(
        y=audio,
        sr=sr,
        units="frames",
        hop_length=HOP_LENGTH,
        backtrack=False,
        pre_max=3,
        post_max=3,
        pre_avg=8,
        post_avg=8,
        delta=0.07,
        wait=1,
    )
    return librosa.frames_to_time(onset_frames, sr=sr, hop_length=HOP_LENGTH)


def _dedupe_onsets(onset_times: np.ndarray) -> np.ndarray:
    kept = []
    for onset_time in onset_times:
        if not kept or onset_time - kept[-1] >= LIBROSA_MIN_ONSET_GAP:
            kept.append(float(onset_time))
    return np.asarray(kept)


def _estimate_f0(audio: np.ndarray, sr: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    return librosa.pyin(
        audio,
        fmin=librosa.midi_to_hz(GUITAR_MIDI_MIN),
        fmax=librosa.midi_to_hz(GUITAR_MIDI_MAX),
        sr=sr,
        hop_length=HOP_LENGTH,
    )


def _compute_cqt(audio: np.ndarray, sr: int) -> tuple[np.ndarray, np.ndarray]:
    n_bins = 72
    fmin = librosa.note_to_hz("C2")
    cqt = np.abs(librosa.cqt(audio, sr=sr, fmin=fmin, hop_length=HOP_LENGTH, n_bins=n_bins, bins_per_octave=12))
    freqs = librosa.cqt_frequencies(n_bins=n_bins, fmin=fmin, bins_per_octave=12)
    return cqt, freqs


def _build_librosa_note_events(
    onset_times: np.ndarray,
    f0: np.ndarray,
    voiced_flag: np.ndarray,
    voiced_prob: np.ndarray,
    cqt_mag: np.ndarray,
    freqs: np.ndarray,
    sr: int,
) -> list[dict]:
    note_events = []
    n_frames = cqt_mag.shape[1]

    for i, onset_time in enumerate(onset_times):
        next_onset = float(onset_times[i + 1]) if i + 1 < len(onset_times) else (n_frames - 1) * HOP_LENGTH / sr
        end_time = next_onset

        if end_time - onset_time < MIN_NOTE_DURATION:
            continue

        onset_frame = librosa.time_to_frames(onset_time, sr=sr, hop_length=HOP_LENGTH)
        end_frame = librosa.time_to_frames(end_time, sr=sr, hop_length=HOP_LENGTH)
        onset_frame = min(onset_frame, n_frames - 1)
        end_frame = min(end_frame, n_frames)

        if onset_frame >= end_frame:
            continue

        midi_note = _segment_pitch(onset_frame, end_frame, f0, voiced_flag, voiced_prob)
        if midi_note is None:
            midi_note = _cqt_fallback_pitch(onset_frame, end_frame, cqt_mag, freqs)

        if not (GUITAR_MIDI_MIN <= midi_note <= GUITAR_MIDI_MAX):
            continue

        # Follow energy at the detected fundamental rather than assuming the
        # note lasts until the next attack. Require three low-energy frames.
        pitch_bin = int(np.argmin(np.abs(librosa.hz_to_midi(freqs) - midi_note)))
        envelope = cqt_mag[pitch_bin, onset_frame:end_frame]
        if len(envelope) > 3 and envelope.max() > 0:
            peak_frame = int(np.argmax(envelope))
            threshold = envelope.max() * 0.15
            for frame in range(peak_frame + 1, len(envelope) - 2):
                candidate_end = (onset_frame + frame) * HOP_LENGTH / sr
                if candidate_end - onset_time >= MIN_NOTE_DURATION and np.all(envelope[frame:frame + 3] < threshold):
                    end_time = min(end_time, candidate_end)
                    break

        note_events.append({
            "start": float(onset_time),
            "end": float(end_time),
            "pitch": midi_note,
        })

    return note_events


def _segment_pitch(
    onset_frame: int,
    end_frame: int,
    f0: np.ndarray,
    voiced_flag: np.ndarray,
    voiced_prob: np.ndarray,
) -> int | None:
    start = min(onset_frame + 1, len(f0))
    end = min(max(start + 1, end_frame), len(f0))
    if start >= end:
        return None

    valid = voiced_flag[start:end] & np.isfinite(f0[start:end]) & (voiced_prob[start:end] >= 0.35)
    if not np.any(valid):
        return None

    pitches = np.rint(librosa.hz_to_midi(f0[start:end][valid])).astype(int)
    weights = voiced_prob[start:end][valid]
    # A confidence-weighted mode avoids a median falling between two pitches.
    candidates = np.unique(pitches)
    return int(max(candidates, key=lambda pitch: weights[pitches == pitch].sum()))


def _cqt_fallback_pitch(
    onset_frame: int,
    end_frame: int,
    cqt_mag: np.ndarray,
    freqs: np.ndarray,
) -> int:
    segment = cqt_mag[:, onset_frame:end_frame]
    mean_mag = segment.mean(axis=1)
    peak_bin = int(mean_mag.argmax())
    corrected_bin = _prefer_lower_harmonic(peak_bin, mean_mag)
    freq = freqs[corrected_bin]
    return int(round(librosa.hz_to_midi(freq)))


def _prefer_lower_harmonic(peak_bin: int, mean_mag: np.ndarray) -> int:
    peak_mag = mean_mag[peak_bin]
    for octave_bins in (12, 24):
        lower_bin = peak_bin - octave_bins
        if lower_bin >= 0 and mean_mag[lower_bin] >= peak_mag * 0.35:
            return lower_bin
    return peak_bin


def _merge_repeated_notes(note_events: list[dict]) -> list[dict]:
    if not note_events:
        return []

    merged = [note_events[0].copy()]
    for event in note_events[1:]:
        prev = merged[-1]
        gap = event["start"] - prev["end"]
        pitch_diff = abs(event["pitch"] - prev["pitch"])

        if gap <= MERGE_GAP and pitch_diff <= MERGE_PITCH_TOLERANCE:
            prev["end"] = max(prev["end"], event["end"])
            continue

        merged.append(event.copy())

    return merged
