from agents.tools.catalog import CatalogTool
from agents.tools.financing import calculate_financing
import pytest

@pytest.fixture
def catalog(populated_db):
    tool = CatalogTool()
    yield tool
    tool.close()

def test_catalog_fuzzy_search(catalog):
    # Test 1: Fuzzy Search (Typo)
    # "Chvrolet" -> "Chevrolet"
    # "Aveo" is in populated_db
    results = catalog.search_cars(make="Chvrolet", model="Aveo")
    assert len(results) > 0
    assert results[0].make == "Chevrolet"
    assert results[0].model == "Aveo"

def test_catalog_price_range(catalog):
    # Test 2: Price Range
    # We have cars at 180k, 210k, 220k.
    # Target 200k +/- 10% (180k - 220k)
    results = catalog.get_price_range_suggestions(200000)
    assert len(results) >= 1
    prices = [c.price for c in results]
    assert 210000 in prices # Nissan Versa
    # 180k is exactly on the border (200k - 10% = 180k). 
    # 220k is exactly on the border (200k + 10% = 220k).
    # Depending on implementation (<= vs <), they might be included.

def test_financing_tool():
    # Test 3: Financing (Logic only, no DB needed really, but kept here)
    price = 200000
    plan = calculate_financing(price, down_payment=40000, years=4)
    assert plan['down_payment'] == 40000
    assert plan['months'] == 48
    assert plan['monthly_payment'] > 0
