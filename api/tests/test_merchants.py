import math
from collections.abc import AsyncIterator

import psycopg
import pytest
import pytest_asyncio

# The module, not its names: the file collects as soon as merchants.py exists, and each test
# turns green with the task that builds what it calls.
from app import merchants
from app.db import Store, make_pool
from app.load_world import load


@pytest_asyncio.fixture
async def store(world_db: str) -> AsyncIterator[Store]:
    """A Store over a small pool on the loaded test world. Local: conftest.py is out of scope."""
    async with make_pool(world_db) as pool:
        yield Store(pool)


# Every distinct descriptor in data/world.json, with what is left once the noise is gone.
WORLD_DESCRIPTORS = [
    ("NORTHWIND RUNNING #0412 PORTLAND OR", "NORTHWIND RUNNING PORTLAND"),
    ("SQ *COBALT COFFEE ROA", "COBALT COFFEE ROA"),
    ("SQ *RUNNERS DEPOT", "RUNNERS DEPOT"),
    ("MERIDIAN ELEC 800-555-0199", "MERIDIAN ELEC"),
    ("FIELDSTONE OUTF*ORDER 7731", "FIELDSTONE OUTF"),
    ("HARBOR&PINE CHI", "HARBOR AND PINE CHI"),
    ("SKYLINE AIR 0062140088812", "SKYLINE AIR"),
    ("SKYLINE AIR 0062140077120", "SKYLINE AIR"),
    ("LARKSPUR HOME 877-555-0142 NY", "LARKSPUR HOME"),
    ("VERDE GROCERS DELIV", "VERDE GROCERS DELIV"),
    ("TST* PETAL AND STEM", "PETAL AND STEM"),
    ("SQ *LARKSPUR HOME", "LARKSPUR HOME"),
    ("BRAMBLE BOOKS ONLINE", "BRAMBLE BOOKS ONLINE"),
    ("QUILL OFFICE #22", "QUILL OFFICE"),
    ("MERIDIANELECTRONICS.COM", "MERIDIANELECTRONICS"),
    ("PYMT*SVC 8831204 CA", "PYMT SVC"),
    ("PAYPAL *NWRUNNINGCO", "NWRUNNINGCO"),
    ("LUMEN*STREAMING", "LUMEN STREAMING"),
]


@pytest.mark.parametrize(("descriptor", "expected"), WORLD_DESCRIPTORS)
def test_normalize_cleans_each_world_descriptor(descriptor: str, expected: str) -> None:
    assert merchants.normalize(descriptor) == expected


@pytest.mark.parametrize("prefix", ["SP *", "PY *"])
def test_normalize_strips_the_prefixes_the_world_lacks(prefix: str) -> None:
    assert merchants.normalize(f"{prefix}BRAMBLE BOOKS") == "BRAMBLE BOOKS"


def test_normalize_strips_only_one_prefix() -> None:
    # A second prefix is part of the name we were given, not noise we may guess away.
    assert merchants.normalize("SQ *PAYPAL *BRAMBLE BOOKS") == "PAYPAL BRAMBLE BOOKS"


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (merchants.HIGH, "high"),
        (math.nextafter(merchants.HIGH, 0), "medium"),
        (merchants.MEDIUM, "medium"),
        (math.nextafter(merchants.MEDIUM, 0), "low"),
    ],
    ids=["at HIGH", "just below HIGH", "at MEDIUM", "just below MEDIUM"],
)
def test_band_edges(score: float, expected: str) -> None:
    assert merchants.band(score) == expected


async def test_the_loader_names_only_direct_merchants(world_db: str) -> None:
    first = await load(world_db)
    second = await load(world_db)
    # 24, not 38: names and aliases are stored normalized and de-duplicated.
    assert first["merchant_names"] == second["merchant_names"] == 24
    query = """
        SELECT DISTINCT m.kind
        FROM merchant_names n JOIN merchants m ON m.id = n.merchant_id
    """
    async with await psycopg.AsyncConnection.connect(world_db) as conn:
        cur = await conn.execute(query)
        kinds = [row[0] for row in await cur.fetchall()]
    assert kinds == ["direct"]


@pytest.mark.parametrize(
    ("merchant_id", "descriptor", "expected_id", "expected_method"),
    [
        ("M-NWR", "NORTHWIND RUNNING #0412 PORTLAND OR", "M-NWR", "merchant_of_record"),
        ("M-SQ", "SQ *COBALT COFFEE ROA", "M-CBC", "descriptor"),
    ],
    ids=["a direct merchant of record", "a seller behind Square"],
)
async def test_resolve_seller(
    store: Store, merchant_id: str, descriptor: str, expected_id: str, expected_method: str
) -> None:
    transaction = {"merchant_id": merchant_id, "descriptor": descriptor}
    resolution = await merchants.resolve_seller(store, transaction)
    assert resolution.merchant_id == expected_id
    assert resolution.confidence == "high"
    assert resolution.method == expected_method


async def test_a_thin_descriptor_lists_no_candidates(store: Store) -> None:
    transaction = {"merchant_id": "M-PP", "descriptor": "PAYPAL *NWRUNNINGCO"}
    resolution = await merchants.resolve_seller(store, transaction)
    # PayPal hides the seller and the name left over is too thin to tell. Escalate, don't guess.
    assert resolution.merchant_id is None
    assert resolution.confidence == "low"
    assert resolution.candidates == []


async def test_a_medium_match_names_the_seller(store: Store) -> None:
    # Paul's rule since T5: medium is enough to name a seller; only low names none.
    transaction = {"merchant_id": "M-SQ", "descriptor": "SQ *COBALT"}
    resolution = await merchants.resolve_seller(store, transaction)
    assert resolution.merchant_id == "M-CBC"
    assert resolution.name == "Cobalt Coffee Roasters"
    assert resolution.confidence == "medium"
    assert [c.merchant_id for c in resolution.candidates] == ["M-CBC"]
