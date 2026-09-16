"""安全计算器：同比等数学表达式求值。"""

from app.tools.calculator import safe_eval_math


def test_yoy_expression():
    """(100-80)/80 应正确算出 0.25（25% 同比）。"""
    assert safe_eval_math("(100-80)/80") == 0.25
