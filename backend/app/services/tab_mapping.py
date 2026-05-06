"""
기타 줄/프렛 매핑 모듈

같은 MIDI pitch를 여러 줄/프렛 위치에서 연주할 수 있으므로,
동적 계획법(DP)으로 전체 운지 비용이 최소가 되는 경로를 선택한다.

표준 튜닝 (낮은 줄부터):
  줄 0: E2 (MIDI 40)
  줄 1: A2 (MIDI 45)
  줄 2: D3 (MIDI 50)
  줄 3: G3 (MIDI 55)
  줄 4: B3 (MIDI 59)
  줄 5: e4 (MIDI 64)
"""

OPEN_STRINGS = [40, 45, 50, 55, 59, 64]
MAX_FRET = 19


def map(note_events: list[dict]) -> list[dict]:
    """
    note_events: [{"start", "end", "pitch"}, ...]
    반환: [{"start", "end", "pitch", "string", "fret"}, ...]
    """
    if not note_events:
        return []

    pitches = [e["pitch"] for e in note_events]
    candidates = [_get_candidates(p) for p in pitches]

    # 후보가 없는 음표는 건너뜀 (음역 벗어난 경우)
    valid_indices = [i for i, c in enumerate(candidates) if len(c) > 0]
    if not valid_indices:
        return []

    # 유효한 음표만 DP 수행
    valid_events = [note_events[i] for i in valid_indices]
    valid_candidates = [candidates[i] for i in valid_indices]

    path = _dp_solve(valid_candidates)

    result = []
    for i, j in enumerate(path):
        string_idx, fret = valid_candidates[i][j]
        result.append({
            **valid_events[i],
            "string": string_idx,
            "fret": fret,
        })

    return result


def _get_candidates(midi_note: int) -> list[tuple[int, int]]:
    """주어진 MIDI 음에 대해 가능한 (줄, 프렛) 후보 목록을 반환한다."""
    candidates = []
    for string_idx, open_note in enumerate(OPEN_STRINGS):
        fret = midi_note - open_note
        if 0 <= fret <= MAX_FRET:
            candidates.append((string_idx, fret))
    return candidates


def _transition_cost(prev: tuple[int, int] | None, curr: tuple[int, int]) -> float:
    """
    이전 위치에서 현재 위치로 이동하는 비용을 계산한다.

    비용 구성:
    - 프렛 이동 거리 (손 포지션 이동)
    - 줄 이동량
    - 낮은 프렛 선호 (열린 줄 포함)
    - 큰 점프 패널티
    """
    curr_string, curr_fret = curr

    if prev is None:
        # 첫 음: 낮은 포지션 선호
        return curr_fret * 0.5

    prev_string, prev_fret = prev
    fret_dist = abs(curr_fret - prev_fret)
    string_dist = abs(curr_string - prev_string)

    cost = fret_dist * 2.0 + string_dist * 0.5 + curr_fret * 0.1

    # 5프렛 이상 이동 시 추가 패널티
    if fret_dist > 5:
        cost += (fret_dist - 5) * 3.0

    return cost


def _dp_solve(candidates: list[list[tuple[int, int]]]) -> list[int]:
    """DP로 최소 비용 경로를 구해 각 음표에서 선택한 후보 인덱스 목록을 반환한다."""
    n = len(candidates)
    INF = float("inf")

    dp = [[INF] * len(c) for c in candidates]
    parent = [[-1] * len(c) for c in candidates]

    # 초기화: 첫 번째 음표
    for j, pos in enumerate(candidates[0]):
        dp[0][j] = _transition_cost(None, pos)

    # 점화식
    for i in range(1, n):
        for j, curr_pos in enumerate(candidates[i]):
            for k, prev_pos in enumerate(candidates[i - 1]):
                cost = dp[i - 1][k] + _transition_cost(prev_pos, curr_pos)
                if cost < dp[i][j]:
                    dp[i][j] = cost
                    parent[i][j] = k

    # 역추적
    last_j = int(min(range(len(candidates[n - 1])), key=lambda j: dp[n - 1][j]))
    path = [last_j]
    for i in range(n - 1, 0, -1):
        last_j = parent[i][last_j]
        path.append(last_j)

    path.reverse()
    return path
