from app.tools.calculator import safe_eval_math


def test_yoy_expression():
    assert safe_eval_math("(100-80)/80") == 0.25
