import numpy as np
import librosa

# 기타 연주 가능 MIDI 음역: E2(40) ~ E6(88)
GUITAR_MIDI_MIN = 40
GUITAR_MIDI_MAX = 88


def extract_notes(audio: np.ndarray, sr: int) -> list[dict]:
    """
    CQT 기반 pitch 추정 + onset detection으로 note event 목록을 반환한다.

    반환 형식:
        [{"start": float, "end": float, "pitch": int (MIDI note)}, ...]
    """
    onset_times = _detect_onsets(audio, sr)
    if len(onset_times) == 0:
        return []

    cqt_mag, freqs = _compute_cqt(audio, sr)
    note_events = _build_note_events(onset_times, cqt_mag, freqs, sr)
    return note_events


def _detect_onsets(audio: np.ndarray, sr: int) -> np.ndarray:
    onset_frames = librosa.onset.onset_detect(
        y=audio,
        sr=sr,
        units="frames",
        hop_length=512,
        backtrack=True,
    )
    onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=512)
    return onset_times


def _compute_cqt(audio: np.ndarray, sr: int) -> tuple[np.ndarray, np.ndarray]:
    n_bins = 72  # 6 octaves × 12 bins
    cqt = np.abs(librosa.cqt(audio, sr=sr, hop_length=512, n_bins=n_bins, bins_per_octave=12))
    freqs = librosa.cqt_frequencies(n_bins=n_bins, fmin=librosa.note_to_hz("C2"), bins_per_octave=12)
    return cqt, freqs


def _build_note_events(
    onset_times: np.ndarray,
    cqt_mag: np.ndarray,
    freqs: np.ndarray,
    sr: int,
) -> list[dict]:
    note_events = []
    n_frames = cqt_mag.shape[1]

    for i, onset_time in enumerate(onset_times):
        end_time = float(onset_times[i + 1]) if i + 1 < len(onset_times) else onset_time + 0.5

        onset_frame = librosa.time_to_frames(onset_time, sr=sr, hop_length=512)
        end_frame = librosa.time_to_frames(end_time, sr=sr, hop_length=512)
        onset_frame = min(onset_frame, n_frames - 1)
        end_frame = min(end_frame, n_frames)

        if onset_frame >= end_frame:
            continue

        segment = cqt_mag[:, onset_frame:end_frame]
        mean_mag = segment.mean(axis=1)
        peak_bin = int(mean_mag.argmax())
        freq = freqs[peak_bin]

        midi_note = int(round(librosa.hz_to_midi(freq)))
        if not (GUITAR_MIDI_MIN <= midi_note <= GUITAR_MIDI_MAX):
            continue

        note_events.append({
            "start": float(onset_time),
            "end": float(end_time),
            "pitch": midi_note,
        })

    return note_events
