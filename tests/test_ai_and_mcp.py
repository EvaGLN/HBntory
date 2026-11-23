import asyncio
import json
import pytest

from mcp.server.fastmcp.exceptions import ToolError
from sqlalchemy.orm import sessionmaker

import product_server

from ai_app import create_ai_app
from models import create_tables, make_engine
from products_client import ProductClient
from seed import seed
from stock_queries import branch_stock, plan_shopping_list, where_is_product


@pytest.fixture
def db(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path}/ai.db")
    create_tables(engine)
    session = sessionmaker(engine)()
    seed(session, "adminpass1")
    yield session
    session.close()


def call_tool(name, args):
    return asyncio.run(product_server.mcp.call_tool(name, args))


def test_stock_queries(db):
    assert where_is_product(db, "HB-LAP-1001") == [
        {"branch": "Lyon", "quantity": 2},
        {"branch": "Toulouse", "quantity": 10}
    ]
    assert where_is_product(db, "ZZZ") == []
    assert [p["product_id"] for p in branch_stock(db, "Lyon")["products"]] == [
        "HB-KBD-4101",
        "HB-LAP-1001",
    ]
    assert branch_stock(db, "Nowhere") is None


@pytest.mark.parametrize(
    "wanted,single,satisfiable",
    [
        ({"HB-LAP-1001": 3, "HB-MON-2101": 2}, ["Toulouse"], True),
        ({"HB-LAP-1001": 12}, [], True),
        ({"HB-MON-2101": 3, "HB-KBD-4101": 7}, [], True),
        ({"HB-LAP-1001": 50}, [], False),
    ],
)
def test_shopping_list(db, wanted, single, satisfiable):
    plan = plan_shopping_list(db, wanted)
    assert plan["satisfiable"] is satisfiable and plan["single_branch"] ==\
        single

    if satisfiable:
        for pid, need in wanted.items():
            assert sum(items.get(pid, 0) for items in plan["plan"].values())\
                == need
    else:
        assert plan["missing"] == {"HB-LAP-1001": 38}


def test_ask_endpoint():
    c = create_ai_app(lambda q: f"echo: {q}").test_client()
    assert c.post("/ask", json={"question": "hi"}).get_json() ==\
        {"answer": "echo: hi"}
    assert c.post("/ask", json={"question": " "}).status_code == 400
    assert c.post("/ask", json={"question": 5}).status_code == 400
    assert c.post("/ask", json={"question": "x" * 501}).status_code == 400

    def slow(q):
        raise TimeoutError

    assert (
        create_ai_app(slow)
        .test_client()
        .post("/ask", json={"question": "x"})
        .status_code
        == 504
    )

    def boom(q):
        raise RuntimeError("down")

    assert (
        create_ai_app(boom)
        .test_client()
        .post("/ask", json={"question": "x"})
        .status_code
        == 502
    )


def test_mcp_tools(product_api_url):
    product_server.client = ProductClient(product_api_url)
    assert (
        json.loads(call_tool("get_product", {"product_id": "HB-LAP-1001"})[0].text)[
            "product"
        ]["name"]
        == "Laptop"
    )

    assert len(json.loads(call_tool("list_products", {})[0].text)["products"])\
        == 3

    with pytest.raises(ToolError, match="No product"):
        call_tool("get_product", {"product_id": "ZZZ"})

    product_server.client = ProductClient("http://127.0.0.2:9")

    with pytest.raises(ToolError, match="unavailable"):
        call_tool("list_products", {})
