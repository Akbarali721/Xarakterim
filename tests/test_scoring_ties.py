"""Weighted scoring and tie handling."""

from app.services.personality_scoring import calculate_personality_result


def test_exact_total_tie_uses_strong_votes_not_first_pole():
    """Equal E/I totals: stronger side wins; no default E."""
    result = calculate_personality_result(
        9,
        9,
        10,
        5,
        8,
        8,
        7,
        7,
        strong_e=6,
        strong_i=9,
        tie_salt="test-token",
    )
    assert result.result_type[0] == "I"
    assert result.ei.low_confidence is True


def test_exact_tie_without_strong_bias_uses_stable_salt_not_always_e():
    """Different salts can land on either letter. The same salt never flips."""
    salts = [f"tie-salt-{n}" for n in range(32)]
    letters = {
        calculate_personality_result(6, 6, 12, 6, 12, 6, 12, 6, tie_salt=s).result_type[0] for s in salts
    }
    assert "E" in letters and "I" in letters
    first = calculate_personality_result(6, 6, 12, 6, 12, 6, 12, 6, tie_salt="session-abc")
    second = calculate_personality_result(6, 6, 12, 6, 12, 6, 12, 6, tie_salt="session-abc")
    assert first.result_type == second.result_type
    assert first.ei.low_confidence is True


def test_complete_tie_letter_matches_sha256_not_process_hash():
    import hashlib

    salt = "fixed-tie-salt"
    payload = f"{salt}:ei\0E\0I".encode()
    expected = "E" if hashlib.sha256(payload).digest()[0] % 2 == 0 else "I"
    result = calculate_personality_result(6, 6, 12, 6, 12, 6, 12, 6, tie_salt=salt)
    assert result.result_type[0] == expected
    assert result.ei.low_confidence is True


def test_close_score_stays_low_confidence_and_keeps_the_higher_side():
    close = calculate_personality_result(8, 6, 12, 6, 12, 6, 12, 6, tie_salt="close")
    assert close.result_type[0] == "E"
    assert close.ei.low_confidence is True

    clear = calculate_personality_result(9, 6, 12, 6, 12, 6, 12, 6, tie_salt="close")
    assert clear.result_type[0] == "E"
    assert clear.ei.low_confidence is False


def test_clear_winner_not_low_confidence():
    result = calculate_personality_result(18, 6, 12, 6, 12, 6, 12, 6, tie_salt="x")
    assert result.result_type[0] == "E"
    assert result.ei.low_confidence is False
