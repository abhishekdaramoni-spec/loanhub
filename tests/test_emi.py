import pytest
from app.services.emi_service import EMIService
from decimal import Decimal

def test_standard_emi_calculation():
    # principal = 100,000, interest = 12% p.a., tenure = 12 months
    res = EMIService.calculate_emi(100000, 12, 12)
    assert res['monthly_emi'] == Decimal('8884.88')
    assert res['total_payable'] == Decimal('106618.56')
    assert res['total_interest'] == Decimal('6618.56')

def test_zero_interest_emi_calculation():
    # principal = 120,000, interest = 0% p.a. (promo), tenure = 12 months
    res = EMIService.calculate_emi(120000, 0, 12)
    assert res['monthly_emi'] == Decimal('10000.00')
    assert res['total_payable'] == Decimal('120000.00')
    assert res['total_interest'] == Decimal('0.00')

def test_invalid_emi_inputs():
    # Principal must be positive
    with pytest.raises(ValueError):
        EMIService.calculate_emi(-1000, 10, 12)
        
    # Rate cannot be negative
    with pytest.raises(ValueError):
        EMIService.calculate_emi(1000, -5, 12)
        
    # Tenure must be positive
    with pytest.raises(ValueError):
        EMIService.calculate_emi(1000, 10, 0)

def test_amortization_schedule():
    schedule = EMIService.generate_amortization_schedule(120000, 0, 12)
    assert len(schedule) == 12
    for month in schedule:
        assert month['emi'] == Decimal('10000.00')
        assert month['principal_paid'] == Decimal('10000.00')
        assert month['interest_paid'] == Decimal('0.00')
    
    # Last month balance must be 0
    assert schedule[-1]['balance_remaining'] == Decimal('0.00')
