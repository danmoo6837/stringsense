import unittest
import numpy as np
import librosa
from app.services.rhythm import analyze


class RhythmTests(unittest.TestCase):
    def test_silence_uses_explicit_fallback(self):
        result = analyze(np.zeros(22050), 22050)
        self.assertEqual(result["tempo_source"], "fallback")
        self.assertEqual(result["bpm"], 120)
        self.assertEqual(result["bar_boundaries"][0], 0)
        self.assertGreaterEqual(result["bar_boundaries"][-1], 1)

    def test_click_track_tempo_and_covering_grid(self):
        sr = 22050
        audio = librosa.clicks(times=np.arange(.25, 12, .5), sr=sr, length=12 * sr)
        result = analyze(audio, sr)
        self.assertEqual(result["tempo_source"], "estimated")
        self.assertAlmostEqual(result["bpm"], 120, delta=5)
        boundaries = result["bar_boundaries"]
        self.assertEqual(boundaries[0], 0)
        self.assertGreaterEqual(boundaries[-1], 12)
        self.assertTrue(all(a < b for a, b in zip(boundaries, boundaries[1:])))


if __name__ == "__main__":
    unittest.main()
