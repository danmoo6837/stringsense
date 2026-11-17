import tempfile
import unittest
import xml.etree.ElementTree as ET
from app.services.tab_pdf import to_musicxml, quantize


def event(start=0, end=.5, pitch=64, string=5, fret=0):
    return dict(start=start, end=end, pitch=pitch, string=string, fret=fret)


class MusicXmlTests(unittest.TestCase):
    def score(self, events, rhythm=None):
        with tempfile.TemporaryDirectory() as directory:
            return ET.parse(to_musicxml(events, directory, rhythm)).getroot()

    def test_empty_measures_are_full_rests(self):
        root = self.score([])
        self.assertEqual(len(root.findall("part")), 2)
        for part in root.findall("part"):
            for note in part.findall("measure/note"):
                self.assertIsNotNone(note.find("rest"))
                self.assertEqual(note.findtext("duration"), "16")

    def test_guitar_written_octave_and_tab_fingering(self):
        root = self.score([event(pitch=61, string=4, fret=2)])
        note = root.find("part/measure/note")
        self.assertEqual(note.findtext("pitch/step"), "C")
        self.assertEqual(note.findtext("pitch/alter"), "1")
        self.assertEqual(note.findtext("pitch/octave"), "5")
        tab = root.findall("part")[1].find("measure/note")
        self.assertEqual(tab.findtext("notations/technical/string"), "2")
        self.assertEqual(tab.findtext("notations/technical/fret"), "2")
        self.assertEqual(tab.findtext("pitch/octave"), "4")

    def test_low_open_e_is_written_e3_and_sounds_e2(self):
        root = self.score([event(pitch=40, string=0, fret=0)])
        part = root.find("part")
        self.assertEqual(part.findtext("measure/note/pitch/step"), "E")
        self.assertEqual(part.findtext("measure/note/pitch/octave"), "3")
        self.assertEqual(part.findtext("measure/attributes/transpose/octave-change"), "-1")

    def test_cross_bar_note_is_tied_and_voices_fill_measures(self):
        root = self.score([event(start=1.5, end=2.5), event(start=1.75, end=2.25, pitch=55, string=3)])
        self.assertTrue(root.findall(".//tie[@type='start']"))
        self.assertTrue(root.findall(".//tie[@type='stop']"))
        for part in root.findall("part"):
            for measure in part.findall("measure"):
                totals = {}
                for note in measure.findall("note"):
                    if note.find("chord") is None:
                        voice = note.findtext("voice")
                        totals[voice] = totals.get(voice, 0) + int(note.findtext("duration"))
                self.assertTrue(all(total == 16 for total in totals.values()))

    def test_actual_beat_grid_is_used(self):
        rhythm = dict(bpm=120, bar_boundaries=[0, 2.2], beat_times=[0, .6, 1.2, 1.7, 2.2])
        notes, _, _ = quantize([event(start=.6, end=1.2)], rhythm)
        self.assertEqual((notes[0]["tick_start"], notes[0]["tick_end"]), (4, 8))

    def test_same_pitch_reattack_ends_previous_note(self):
        notes, _, _ = quantize([event(0, 1), event(.5, 1.5)])
        self.assertEqual(notes[0]["tick_end"], notes[1]["tick_start"])

    def test_two_measures_per_system(self):
        root = self.score([event(end=9)])
        for part in root.findall("part"):
            breaks = [m.get("number") for m in part.findall("measure")
                      if m.find("print[@new-system='yes']") is not None]
            self.assertEqual(breaks, ["3", "5"])


if __name__ == "__main__":
    unittest.main()
