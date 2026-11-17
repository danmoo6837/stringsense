import unittest
from unittest.mock import patch, Mock
import sys
import types
import numpy as np
from app.services import transcribe


class TranscriptionTests(unittest.TestCase):
    def test_basic_pitch_is_preferred(self):
        notes = [dict(start=0., end=.5, pitch=60)]
        with patch.object(transcribe, "_extract_with_basic_pitch", return_value=notes), patch.object(transcribe, "_extract_with_librosa") as fallback:
            self.assertEqual(transcribe.extract_notes(np.zeros(10), 22050, "sample.wav"), notes)
            fallback.assert_not_called()

    def test_empty_basic_pitch_stays_empty(self):
        with patch.object(transcribe, "_extract_with_basic_pitch", return_value=[]), patch.object(transcribe, "_extract_with_librosa", return_value=[]) as fallback:
            self.assertEqual(transcribe.extract_notes(np.zeros(10), 22050, "sample.wav"), [])
            fallback.assert_not_called()

    def test_failed_prediction_stays_empty(self):
        inference = types.ModuleType("basic_pitch.inference")
        inference.predict = Mock(side_effect=RuntimeError("prediction failed"))
        with patch.dict(sys.modules, {"basic_pitch.inference": inference}), patch.object(transcribe, "_extract_with_librosa") as fallback:
            with self.assertLogs(level="WARNING"):
                self.assertEqual(transcribe.extract_notes(np.zeros(10), 22050, "sample.wav"), [])
            inference.predict.assert_called_once_with("sample.wav")
            fallback.assert_not_called()

    def test_fast_attacks_are_retained(self):
        np.testing.assert_allclose(transcribe._dedupe_onsets(np.array([0., .08, .16])), [0., .08, .16])

    def test_confidence_mode_does_not_invent_middle_pitch(self):
        f0 = np.array([440., 440., 440., 523.251, 523.251])
        pitch = transcribe._segment_pitch(0, 5, f0, np.ones(5, dtype=bool), np.array([1., .9, .9, .4, .4]))
        self.assertEqual(pitch, 69)

    def test_missing_path_stays_empty(self):
        audio = np.zeros(22050)
        with patch.object(transcribe, "_extract_with_librosa") as extract:
            self.assertEqual(transcribe.extract_notes(audio, 22050), [])
            extract.assert_not_called()
