import pytest
from app import create_app
from app.utils.extensions import db as _db
from app.models import User, LoanType, LoanApplication, InterestRate, FAQ

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app('testing')
    
    with app.app_context():
        _db.create_all()
        
        # Seed basic LoanType required for testing submissions
        personal_loan = LoanType(
            name="Personal Loan",
            slug="personal-loan",
            description="Test personal loan.",
            category="Retail",
            min_amount=10000,
            max_amount=500000,
            min_interest_rate=10.0,
            max_interest_rate=15.0,
            processing_fee_pct=1.0,
            min_tenure_months=12,
            max_tenure_months=60,
            eligibility_criteria="Min INR 20k income",
            approval_time="24 Hours"
        )
        _db.session.add(personal_loan)
        _db.session.commit()
        
        yield app
        
        _db.session.remove()
        _db.drop_all()

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def db(app):
    """The database instance."""
    return _db
