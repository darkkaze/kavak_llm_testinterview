from agents.tools.financing import calculate_financing

def test_calculate_financing_defaults():
    """Test with default down payment (20%) and 4 years."""
    price = 200000
    plan = calculate_financing(price, years=4)
    
    expected_down = 40000 # 20%
    # expected_principal = 160000
    # expected_interest = 160000 * 0.10 * 4 # 64,000
    # expected_total = 160000 + 64000 # 224,000
    # expected_monthly = 224000 / 48 # 4,666.66...
    
    assert plan["down_payment"] == expected_down
    assert plan["months"] == 48
    assert abs(plan["monthly_payment"] - 4666.67) < 0.01
    assert abs(plan["total_paid"] - 264000.0) < 0.01

def test_calculate_financing_custom_down():
    """Test with custom down payment."""
    price = 300000
    down = 100000
    plan = calculate_financing(price, down_payment=down, years=3)
    
    # expected_principal = 200000
    # expected_interest = 200000 * 0.10 * 3 # 60,000
    # expected_total = 260000
    # expected_monthly = 260000 / 36 # 7222.22
    
    assert plan["down_payment"] == down
    assert abs(plan["monthly_payment"] - 7222.22) < 0.01
