import unittest
from unittest.mock import patch
import numpy as np
from app.services import transcribe


class TranscriptionTests(unittest.TestCase):
    def test_basic_pitch_is_preferred(self):
        notes = [dict(start=0., end=.5, pitch=60)]
        with patch.object(transcribe, "_extract_with_basic_pitch", return_value=notes), patch.object(transcribe, "_extract_with_librosa") as fallback:
            self.assertEqual(transcribe.extract_notes(np.zeros(10), 22050, "sample.wav"), notes)
            fallback.assert_not_called()

    def test_empty_basic_pitch_falls_back(self):
        with patch.object(transcribe, "_extract_with_basic_pitch", return_value=[]), patch.object(transcribe, "_extract_with_librosa", return_value=[]) as fallback:
            self.assertEqual(transcribe.extract_notes(np.zeros(10), 22050, "sample.wav"), [])
            fallback.assert_called_once()

    def test_fast_attacks_are_retained(self):
        np.testing.assert_allclose(transcribe._dedupe_onsets(np.array([0., .08, .16])), [0., .08, .16])

    def test_confidence_mode_does_not_invent_middle_pitch(self):
        f0 = np.array([440., 440., 440., 523.251, 523.251])
        pitch = transcribe._segment_pitch(0, 5, f0, np.ones(5, dtype=bool), np.array([1., .9, .9, .4, .4]))
        self.assertEqual(pitch, 69)

    def test_public_extractor_uses_librosa(self):
        audio = np.zeros(22050)
        expected = [dict(start=0, end=0.5, pitch=60)]
        with patch.object(transcribe, "_extract_with_librosa", return_value=expected) as extract:
            self.assertEqual(transcribe.extract_notes(audio, 22050), expected)
            extract.assert_called_once_with(audio, 22050)
