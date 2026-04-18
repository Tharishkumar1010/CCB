from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Tuple
import math

# ------------------------------------------------------------
# Optional Graphviz Support
# ------------------------------------------------------------
try:
    from graphviz import Digraph
    GRAPHVIZ_AVAILABLE = True
except Exception:
    GRAPHVIZ_AVAILABLE = False


# ------------------------------------------------------------
# Expression Tree
# ------------------------------------------------------------
@dataclass(frozen=True)
class Expr:
    op: str
    left: "Expr | None" = None
    right: "Expr | None" = None
    name: str | None = None
    prob: Fraction | None = None

    def value(self) -> Fraction:
        if self.op == "SRC":
            return self.prob
        if self.op == "CONST0":
            return Fraction(0)
        if self.op == "CONST1":
            return Fraction(1)
        if self.op == "NOT":
            return 1 - self.left.value()
        if self.op == "AND":
            return self.left.value() * self.right.value()
        raise ValueError(f"Unknown op: {self.op}")

    def size(self) -> int:
        if self.op in {"SRC", "CONST0", "CONST1"}:
            return 1
        if self.op == "NOT":
            return 1 + self.left.size()
        if self.op == "AND":
            return 1 + self.left.size() + self.right.size()

    def to_text(self) -> str:
        if self.op == "SRC":
            return self.name
        if self.op == "CONST0":
            return "0"
        if self.op == "CONST1":
            return "1"
        if self.op == "NOT":
            return f"NOT({self.left.to_text()})"
        if self.op == "AND":
            return f"AND({self.left.to_text()}, {self.right.to_text()})"

    def canonical(self) -> str:
        if self.op == "SRC":
            return self.name
        if self.op == "CONST0":
            return "0"
        if self.op == "CONST1":
            return "1"
        if self.op == "NOT":
            return f"N({self.left.canonical()})"
        if self.op == "AND":
            a, b = self.left.canonical(), self.right.canonical()
            return f"A({min(a,b)},{max(a,b)})"


def SRC(name: str, p: Fraction) -> Expr:
    return Expr("SRC", name=name, prob=p)

def CONST0() -> Expr:
    return Expr("CONST0")

def CONST1() -> Expr:
    return Expr("CONST1")

def NOT(x: Expr) -> Expr:
    return Expr("NOT", left=x)

def AND(x: Expr, y: Expr) -> Expr:
    return Expr("AND", left=x, right=y) if x.canonical() <= y.canonical() else Expr("AND", left=y, right=x)


def to_fraction(decimal_str: str) -> Fraction:
    return Fraction(Decimal(decimal_str))

def score(expr: Expr, target: Fraction) -> Tuple[Fraction, int, int]:
    return (abs(expr.value() - target), expr.size(), len(expr.to_text()))

def prune_best(expressions: List[Expr]) -> Dict[Fraction, Expr]:
    best = {}
    for e in expressions:
        val = e.value()
        if val not in best or (e.size(), len(e.to_text())) < (best[val].size(), len(best[val].to_text())):
            best[val] = e
    return best


def search_expression(target_str: str, rounds=7, beam_width=250, pair_limit=180) -> Expr:
    target = to_fraction(target_str)

    A = SRC("A", Fraction(2, 5))
    B = SRC("B", Fraction(1, 2))

    beam = [A, B, NOT(A), NOT(B)]
    known = prune_best(beam)

    best_expr = min(beam, key=lambda e: score(e, target))

    for _ in range(rounds):
        beam = sorted(beam, key=lambda e: score(e, target))[:beam_width]
        pool = beam[:pair_limit]

        new = []
        new.extend([NOT(e) for e in pool])

        for i in range(len(pool)):
            for j in range(i, len(pool)):
                new.append(AND(pool[i], pool[j]))

        known = prune_best(list(known.values()) + new)
        beam = sorted(known.values(), key=lambda e: score(e, target))[:beam_width]

        if beam[0].value() == target:
            return beam[0]

    return beam[0]


def build_binary(bits: str) -> Expr:
    H = SRC("H", Fraction(1, 2))
    expr = CONST0()

    for b in reversed(bits):
        expr = AND(H, expr) if b == "0" else NOT(AND(H, NOT(expr)))

    return expr


def draw_expr(expr: Expr, path: str):
    if not GRAPHVIZ_AVAILABLE:
        return

    dot = Digraph(format="png")
    dot.attr(rankdir="LR")

    count = 0

    def add(e: Expr):
        nonlocal count
        count += 1
        nid = f"n{count}"

        dot.node(nid, e.op)

        if e.left:
            l = add(e.left)
            dot.edge(l, nid)
        if e.right:
            r = add(e.right)
            dot.edge(r, nid)

        return nid

    root = add(expr)
    dot.node("OUT", "OUTPUT")
    dot.edge(root, "OUT")

    dot.render(path, cleanup=True)


def print_result(title: str, expr: Expr, target: Fraction | None = None):
    print("="*60)
    print(title)
    print("Expression:", expr.to_text())
    print("Value:", expr.value(), f"({float(expr.value()):.8f})")
    print("Size:", expr.size())

    if target:
        err = abs(expr.value() - target)
        print("Target:", target)
        print("Error:", err, f"({float(err):.8f})")
    print()


def main():
    out = Path("outputs")
    out.mkdir(exist_ok=True)

    targets = ["0.8881188", "0.2119209", "0.5555555"]

    for i, t in enumerate(targets, 1):
        expr = search_expression(t)
        print_result(f"Q2(a).{i}", expr, to_fraction(t))
        draw_expr(expr, str(out / f"q2a_{i}"))

    binaries = ["1011111", "1101111", "1010111"]

    for i, bits in enumerate(binaries, 1):
        expr = build_binary(bits)
        target = sum(Fraction(1, 2**i) for i, b in enumerate(bits, 1) if b == "1")
        print_result(f"Q2(b).{i}", expr, target)
        draw_expr(expr, str(out / f"q2b_{i}"))


if __name__ == "__main__":
    main()
