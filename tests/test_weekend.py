from src.spagent.tools.calendar import current_weekend


def test_current_weekend_order():
    fri, sun = current_weekend()
    assert fri < sun
