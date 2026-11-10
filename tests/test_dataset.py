from app.evaluation.dataset import (load_questions, get_authorized_cases)


def test_get_authorized_cases():
    questions = load_questions()
    cases = get_authorized_cases(questions)

    assert len(cases) == 28
    assert all(case["language"] in ("es", "en") for case in cases)