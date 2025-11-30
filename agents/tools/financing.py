def calculate_financing(car_price: float, down_payment: float = None, years: int = 4):
    """
    Calculates monthly payments based on Kavak's formula:
    - Interest: 10% annual
    - Terms: 3-6 years
    """
    if down_payment is None:
        down_payment = car_price * 0.20 # Default 20%

    principal = car_price - down_payment
    rate = 0.10
    
    # Simple Interest Formula (as per specs: "tasa de interés del 10%")
    # Note: Usually car loans use compound interest/amortization, but specs imply simple calculation or flat rate.
    # "Otorgar planes de financiamiento tomando como base el enganche, el precio del auto, una tasa de interés del 10% y plazos..."
    # Let's assume simple annual interest on the principal for simplicity unless specified otherwise.
    
    total_interest = principal * rate * years
    total_amount = principal + total_interest
    months = years * 12
    monthly_payment = total_amount / months

    return {
        "car_price": car_price,
        "down_payment": down_payment,
        "years": years,
        "months": months,
        "monthly_payment": round(monthly_payment, 2),
        "total_paid": round(total_amount + down_payment, 2)
    }
