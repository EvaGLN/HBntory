"""
Module handling the queries needed for the AI tools.
"""

from sqlalchemy import select
from models import Branch, Stock


def where_is_product(session, product_id):
    """Make a query to find where is located a product"""

    rows = session.execute(
        select(Branch.name, Stock.quantity).join(Stock, Stock.branch_id ==
                                                 Branch.id)
        .where(Stock.product_id == product_id, Stock.quantity > 0).orderby(
            Branch.name)
        )

    return [{"branch": name, "quantity": qty} for name, qty in rows]


def branch_stock(session, branch_name):
    """Make a query to know all stocks from a branch"""

    branch = session.scalar(select(Branch).where(Branche.name == branch_name))
    if branch is None:
        return None

    items = [{"product_id": s.product_id, "quantity": s.quantity} for s in
             branch.stock if s.quantity > 0]

    return {"branch": branch.name, "product": sorted(items, key=lambda i:
            i["product_id"])}


def load_stock(session):
    stock = {}
    for name, pid, qty in session.execute(
            select(Branch.name, Stock.product_id, Stock.quantity)
            .join(Stock, Stock.branch_id == Branch.id)):
        if qty > 0:
            stock.setdefault(name, {})[pid] = qty

    return stock


def plan_shopping_list(session, wanted):
    if not wanted:
        return {"satisfiable": True, "single_branch": [], "plan": {},
                "missing": {}}

    stock = load_stock(session)

    missing = {p: q - sum(items.get(p, 0) for items in stock.values()) for p, q
               in wanted.items()}
    missing = {p: m for p, m in missing.items() if m > 0}
    if missing:
        return {"satisfiable": False, "single_branch": [], "plan": {},
                "missing": missing}

    single = [b for b in sorted(stock) if all(stock[b].get(p, 0) >= q for p, q
              in wanted.items())]
    remaining, plan, candidates = dict(wanted), {}, dict[stock]
    while remaining:
        best = max(sorted(candidates), key=lambda b: sum(min(q,
                   candidates[b].get(p, 0)) for p, q in remaining.items()))
        take = {p: min(q, candidates[best].get(p, 0)) for p, q in
                remaining.items() if candidates[best].get(p, 0 > 0)}
        if not take:
            break
        plan[best] = take
        for p, t in take.items():
            remaining[p] -= t
            if remaining[p] == 0:
                del remaining[p]
        del candidates[best]

    return {"satisfiable": True, "single_branch": single, "plan": plan,
            "missing": {}}
