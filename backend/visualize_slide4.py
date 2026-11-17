"""Render slide assets from an actual backend MIDI and its source audio."""
from pathlib import Path
import numpy as np
import soundfile as sf
import pretty_midi
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/presentation/slide4'
OUT.mkdir(parents=True, exist_ok=True)
audio_path = ROOT / 'backend/data/inputs/audio_mono-mic/solo/00_BN2-166-Ab_solo_mic.wav'
midi_path = ROOT / 'backend/data/outputs/75469531/result.mid'
audio, sr = sf.read(audio_path)
if audio.ndim > 1:
    audio = audio.mean(axis=1)
notes = [n for instrument in pretty_midi.PrettyMIDI(str(midi_path)).instruments
         if not instrument.is_drum for n in instrument.notes]
plt.rcParams.update({'font.family': 'Malgun Gothic', 'font.size': 14,
                     'axes.unicode_minus': False, 'svg.fonttype': 'path'})

def render(name, end):
    fig, (wave, roll) = plt.subplots(2, 1, figsize=(14, 7.4), sharex=True,
                                   gridspec_kw={'height_ratios': [1, 1.7]})
    fig.patch.set_facecolor('white')
    fig.suptitle('오디오에서 음표를 찾는 과정', x=.09, ha='left', fontsize=25, weight='bold')
    # Min/max envelope preserves brief transients when reducing plot size.
    samples = audio[:min(len(audio), int(end * sr))]
    block = max(1, len(samples) // 2400)
    trimmed = samples[:len(samples) // block * block].reshape(-1, block)
    t = (np.arange(len(trimmed)) * block + block / 2) / sr
    wave.fill_between(t, trimmed.min(axis=1), trimmed.max(axis=1), color='#3977b8', linewidth=.3)
    wave.set_title('입력 음원 · Waveform', loc='left', fontsize=16, weight='bold', pad=12)
    wave.set_ylabel('진폭')
    roll.set_title('실제 백엔드 추출 결과 · Piano Roll', loc='left', fontsize=16, weight='bold', pad=12)
    visible = [n for n in notes if n.start < end]
    for n in visible:
        roll.add_patch(Rectangle((n.start, n.pitch - .36), min(n.end, end) - n.start, .72,
                                facecolor='#159c88', edgecolor='#087568', linewidth=.5))
        roll.plot([n.start, n.start], [n.pitch-.36, n.pitch+.36], color='#123e53', linewidth=1.3)
    lo, hi = min(n.pitch for n in visible)-2, max(n.pitch for n in visible)+2
    roll.set_ylim(lo, hi)
    ticks = [p for p in range(lo, hi+1) if p % 12 in (0, 4, 7)]
    roll.set_yticks(ticks, [f'{pretty_midi.note_number_to_name(p)} ({p})' for p in ticks])
    roll.set_ylabel('음높이 (MIDI)')
    roll.set_xlabel('시간 (초)')
    roll.set_xlim(0, end)
    for ax in (wave, roll):
        ax.spines[['top', 'right']].set_visible(False)
        ax.grid(axis='x', alpha=.15)
        ax.set_axisbelow(True)
    roll.grid(axis='y', alpha=.10)
    fig.text(.09, .065, '막대 왼쪽 = 시작 시각(Onset)    ·    세로 위치 = 음높이(Pitch)    ·    막대 길이 = 검출된 지속시간', fontsize=12)
    fig.text(.09, .025, f'00_BN2-166-Ab_solo_mic.wav | 실제 API MIDI · 전체 {len(notes)}음', fontsize=10, color='#64748b')
    fig.subplots_adjust(left=.09, right=.98, top=.86, bottom=.17, hspace=.42)
    for extension in ('png', 'svg', 'pdf'):
        fig.savefig(OUT / f'{name}.{extension}', dpi=220, facecolor='white')
    plt.close(fig)

render('waveform_pianoroll_detail', 8)
render('waveform_pianoroll_full', len(audio) / sr)
(OUT / 'README.md').write_text(
    '# 슬라이드 4 실제 분석 시각화\n\n'
    'detail: 처음 8초 확대, PPT 권장. full: 전체 음원. PNG/SVG/PDF 제공.\n\n'
    f'입력: `{audio_path.relative_to(ROOT).as_posix()}`\n\n'
    f'출력 MIDI: `{midi_path.relative_to(ROOT).as_posix()}`\n\n'
    'MIDI의 실제 음높이와 초 단위 시간을 그대로 표시했다. 악보용 옥타브 이동이나 리듬 양자화를 적용하지 않았다. '
    '막대는 검출 결과이며 정답과의 일치 여부를 나타내지 않는다.\n', encoding='utf-8')
print(OUT)
