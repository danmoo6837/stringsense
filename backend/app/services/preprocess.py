import numpy as np
import librosa

TARGET_SR = 22050
MAX_DURATION = 60.0


def load(path: str) -> tuple[np.ndarray, int]:
    """오디오 파일을 로드하고 분석에 적합한 형태로 정규화한다."""
    audio, sr = librosa.load(path, sr=TARGET_SR, mono=True, duration=MAX_DURATION)

    # peak normalize
    peak = np.abs(audio).max()
    if peak > 0:
        audio = audio / peak

    return audio, sr
