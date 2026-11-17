OPEN_STRINGS = [40, 45, 50, 55, 59, 64]
MAX_FRET = 19

# Prefer stable hand position over simply choosing the lowest fret.
PREFERRED_MAX_FRET = 7
MAX_POSITION_SPAN = 3
FRET_MOVE_WEIGHT = 5.0
STRING_MOVE_WEIGHT = 0.8
SAME_STRING_FAR_MOVE_PENALTY = 8.0
SAME_FRET_DIFFERENT_STRING_BONUS = 2.0


def map(note_events: list[dict]) -> list[dict]:
    if not note_events:
        return []

    candidates = [_get_candidates(event["pitch"]) for event in note_events]
    valid_indices = [i for i, candidate_set in enumerate(candidates) if candidate_set]
    if not valid_indices:
        return []

    valid_events = [note_events[i] for i in valid_indices]
    valid_candidates = [candidates[i] for i in valid_indices]
    path = _dp_solve(valid_candidates)

    result = []
    for i, candidate_index in enumerate(path):
        string_idx, fret = valid_candidates[i][candidate_index]
        result.append({
            **valid_events[i],
            "string": string_idx,
            "fret": fret,
        })

    return result


def _get_candidates(midi_note: int) -> list[tuple[int, int]]:
    candidates = []
    for string_idx, open_note in enumerate(OPEN_STRINGS):
        fret = midi_note - open_note
        if 0 <= fret <= MAX_FRET:
            candidates.append((string_idx, fret))

    return sorted(candidates, key=_candidate_preference)


def _candidate_preference(pos: tuple[int, int]) -> tuple[int, int, int]:
    string_idx, fret = pos
    over_preferred = max(0, fret - PREFERRED_MAX_FRET)
    open_bonus = 0 if fret == 0 else 1
    return over_preferred, open_bonus, fret, string_idx


def _transition_cost(prev: tuple[int, int] | None, curr: tuple[int, int]) -> float:
    curr_string, curr_fret = curr

    cost = _position_cost(curr)
    if prev is None:
        return cost

    prev_string, prev_fret = prev
    fret_dist = abs(curr_fret - prev_fret)
    string_dist = abs(curr_string - prev_string)

    cost += fret_dist * FRET_MOVE_WEIGHT
    cost += string_dist * STRING_MOVE_WEIGHT

    if curr_string == prev_string and fret_dist > MAX_POSITION_SPAN:
        cost += (fret_dist - MAX_POSITION_SPAN) * SAME_STRING_FAR_MOVE_PENALTY

    if curr_string != prev_string and fret_dist <= 1:
        cost -= SAME_FRET_DIFFERENT_STRING_BONUS

    if prev_fret > 0 and curr_fret > 0:
        span = abs(curr_fret - prev_fret)
        if span > MAX_POSITION_SPAN:
            cost += (span - MAX_POSITION_SPAN) * 4.0

    return cost


def _position_cost(pos: tuple[int, int]) -> float:
    _string_idx, fret = pos
    cost = fret * 0.05

    if fret > PREFERRED_MAX_FRET:
        cost += (fret - PREFERRED_MAX_FRET) * 2.0

    return cost


def _dp_solve(candidates: list[list[tuple[int, int]]]) -> list[int]:
    n = len(candidates)
    inf = float("inf")

    dp = [[inf] * len(candidate_set) for candidate_set in candidates]
    parent = [[-1] * len(candidate_set) for candidate_set in candidates]

    for j, pos in enumerate(candidates[0]):
        dp[0][j] = _transition_cost(None, pos)

    for i in range(1, n):
        for j, curr_pos in enumerate(candidates[i]):
            for k, prev_pos in enumerate(candidates[i - 1]):
                cost = dp[i - 1][k] + _transition_cost(prev_pos, curr_pos)
                if cost < dp[i][j]:
                    dp[i][j] = cost
                    parent[i][j] = k

    last_j = int(min(range(len(candidates[n - 1])), key=lambda j: dp[n - 1][j]))
    path = [last_j]
    for i in range(n - 1, 0, -1):
        last_j = parent[i][last_j]
        path.append(last_j)

    path.reverse()
    return path
