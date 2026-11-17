import unittest
from evaluate import score


class EvaluationTests(unittest.TestCase):
    def test_one_to_one_matching(self):
        note = dict(start=1., end=2., pitch=60.)
        result = score([note], [note, note])["onset_pitch"]
        self.assertEqual(result["tp"], 1)
        self.assertEqual(result["fp"], 1)
        self.assertEqual(result["precision"], 0.5)

    def test_offset_scored_separately(self):
        result = score([dict(start=1., end=2., pitch=60.2)], [dict(start=1.02, end=3., pitch=60)])
        self.assertEqual(result["onset_pitch"]["f1"], 1)
        self.assertEqual(result["onset_pitch_offset"]["f1"], 0)

    def test_wrong_pitch_and_empty_predictions(self):
        ref = [dict(start=1., end=2., pitch=60)]
        self.assertEqual(score(ref, [dict(start=1., end=2., pitch=61)])["onset_pitch"]["tp"], 0)
        self.assertEqual(score(ref, [])["onset_pitch"]["fn"], 1)
