"""安全算术计算器：仅解析 AST 数字运算，禁止任意代码执行。"""

from __future__ import annotations

import ast
import operator

from langchain_core.tools import tool

_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _eval_node(node: ast.AST) -> float:
    """递归求值 AST 节点，仅允许常量与二元/一元运算。"""
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return float(_UNARY_OPS[type(node.op)](_eval_node(node.operand)))
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        return float(_BIN_OPS[type(node.op)](left, right))
    raise ValueError("仅允许数字与加减乘除、幂、取余等数学运算")


def safe_eval_math(expr: str) -> float:
    """解析并计算纯算术表达式。"""
    if not expr or not str(expr).strip():
        raise ValueError("表达式不能为空")
    tree = ast.parse(str(expr).strip(), mode="eval")
    return _eval_node(tree)


@tool
def calculator(expression: str) -> str:
    """计算数学表达式。只接受纯算术（如 (100-80)/80），禁止任意代码。"""
    try:
        value = safe_eval_math(expression)
    except Exception as exc:  # noqa: BLE001 — surface parse errors to the agent
        return f"计算失败: {exc}"
    if value == int(value):
        return str(int(value))
    return f"{value:.6g}"
