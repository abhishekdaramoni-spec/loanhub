from datetime import datetime
from decimal import Decimal
from app.utils.extensions import db
from app.models import User, LoanType, InterestRate, FAQ

def seed_default_data():
    """Populates basic tables with core configurations and testing logins if they are empty."""
    # 1. Seed FAQs
    if FAQ.query.count() == 0:
        faqs = [
            FAQ(
                question="What documents are required to apply for a loan?",
                answer="You need a valid PAN Card, Aadhar Card, last 3 months salary slips, and last 6 months bank statements.",
                category="General"
            ),
            FAQ(
                question="How long does it take for loan approval?",
                answer="Retail loans like Personal and Car loans are approved within 24 hours. Mortgages and business loans may take 3 working days.",
                category="Processing"
            ),
            FAQ(
                question="Can I prepay my loan early?",
                answer="Yes, you can prepay your loan after 6 successful EMI payments. Foreclosure charges may apply depending on the loan category.",
                category="Payments"
            )
        ]
        db.session.add_all(faqs)
        db.session.commit()
        print("Default FAQs seeded.")

    # 2. Seed Loan Types
    if LoanType.query.count() == 0:
        loan_types = [
            LoanType(
                name="Personal Loan",
                slug="personal-loan",
                description="Flexible unsecured personal loans for wedding, travel, medical emergencies or debt consolidation.",
                category="Retail",
                min_amount=Decimal('50000.00'),
                max_amount=Decimal('1500000.00'),
                min_interest_rate=Decimal('10.50'),
                max_interest_rate=Decimal('18.00'),
                processing_fee_pct=Decimal('1.50'),
                min_tenure_months=12,
                max_tenure_months=60,
                eligibility_criteria="Minimum salary INR 25,000/month. Age 21-60 years.",
                approval_time="24 Hours",
                icon_class="fa-user-tie"
            ),
            LoanType(
                name="Home Loan",
                slug="home-loan",
                description="Make your dream home a reality with competitive interest rates and extended repayment tenure options.",
                category="Retail",
                min_amount=Decimal('500000.00'),
                max_amount=Decimal('10000000.00'),
                min_interest_rate=Decimal('8.40'),
                max_interest_rate=Decimal('11.00'),
                processing_fee_pct=Decimal('0.50'),
                min_tenure_months=60,
                max_tenure_months=360,
                eligibility_criteria="Salaried or self-employed with minimum annual income of INR 4 Lakhs. Age 21-65 years.",
                approval_time="3 Working Days",
                icon_class="fa-home"
            ),
            LoanType(
                name="Car Loan",
                slug="car-loan",
                description="Drive home your dream car with up to 90% funding on road price and quick documentation.",
                category="Retail",
                min_amount=Decimal('100000.00'),
                max_amount=Decimal('3000000.00'),
                min_interest_rate=Decimal('8.75'),
                max_interest_rate=Decimal('12.50'),
                processing_fee_pct=Decimal('1.00'),
                min_tenure_months=12,
                max_tenure_months=84,
                eligibility_criteria="Minimum monthly income of INR 20,000. Age 18-65 years.",
                approval_time="24 Hours",
                icon_class="fa-car"
            ),
            LoanType(
                name="Education Loan",
                slug="education-loan",
                description="Finance higher education in top domestic and international universities with easy moratorium options.",
                category="Retail",
                min_amount=Decimal('100000.00'),
                max_amount=Decimal('5000000.00'),
                min_interest_rate=Decimal('9.25'),
                max_interest_rate=Decimal('14.00'),
                processing_fee_pct=Decimal('0.00'),
                min_tenure_months=36,
                max_tenure_months=180,
                eligibility_criteria="Indian national with confirmed admission in recognized institute and a co-applicant.",
                approval_time="48 Hours",
                icon_class="fa-graduation-cap"
            ),
            LoanType(
                name="Business Loan",
                slug="business-loan",
                description="Expand your business, purchase inventory or upgrade machinery with collateral-free working capital.",
                category="Commercial",
                min_amount=Decimal('200000.00'),
                max_amount=Decimal('5000000.00'),
                min_interest_rate=Decimal('13.00'),
                max_interest_rate=Decimal('22.00'),
                processing_fee_pct=Decimal('2.00'),
                min_tenure_months=12,
                max_tenure_months=60,
                eligibility_criteria="Business vintage of minimum 3 years with profitable operations and audited balance sheet.",
                approval_time="3 Working Days",
                icon_class="fa-briefcase"
            ),
            LoanType(
                name="Gold Loan",
                slug="gold-loan",
                description="Unlock the value of your gold ornaments with instant disbursement and flexible repayment options.",
                category="Special",
                min_amount=Decimal('10000.00'),
                max_amount=Decimal('2000000.00'),
                min_interest_rate=Decimal('7.90'),
                max_interest_rate=Decimal('11.50'),
                processing_fee_pct=Decimal('0.25'),
                min_tenure_months=6,
                max_tenure_months=24,
                eligibility_criteria="Indian citizen aged 18-70 owning 18-22 karat gold ornaments.",
                approval_time="45 Minutes",
                icon_class="fa-coins"
            ),
            LoanType(
                name="Agriculture Loan",
                slug="agriculture-loan",
                description="Custom financial solutions for crop cultivation, farm equipment purchase and storage infrastructure.",
                category="Agriculture",
                min_amount=Decimal('20000.00'),
                max_amount=Decimal('2500000.00'),
                min_interest_rate=Decimal('4.00'),
                max_interest_rate=Decimal('9.00'),
                processing_fee_pct=Decimal('0.50'),
                min_tenure_months=6,
                max_tenure_months=120,
                eligibility_criteria="Farmer owning agricultural land or lessee with crop cultivation plan.",
                approval_time="48 Hours",
                icon_class="fa-tractor"
            )
        ]
        db.session.add_all(loan_types)
        db.session.commit()
        print("Default Loan Types seeded.")

    # 3. Seed active Interest Rates
    if InterestRate.query.count() == 0:
        l_types = LoanType.query.all()
        rates = []
        for lt in l_types:
            rates.append(InterestRate(
                loan_type_id=lt.id,
                tenure_months=12,
                rate_pct=lt.min_interest_rate,
                status='Active',
                effective_from=datetime.utcnow().date()
            ))
            rates.append(InterestRate(
                loan_type_id=lt.id,
                tenure_months=36,
                rate_pct=lt.min_interest_rate + Decimal('0.50'),
                status='Active',
                effective_from=datetime.utcnow().date()
            ))
        db.session.add_all(rates)
        db.session.commit()
        print("Default Interest Rates seeded.")

    # 4. Seed basic login profiles for testing
    if User.query.count() == 0:
        admin = User(
            name="System Admin",
            email="admin1@loansphere.bank",
            phone="9876543210",
            address="LoanSphere Head Office",
            is_admin=True,
            email_verified=True
        )
        admin.set_password("adminPass1!")

        customer = User(
            name="John Doe",
            email="user1@gmail.com",
            phone="9000000001",
            address="123 Main Street, Delhi",
            is_admin=False,
            email_verified=True
        )
        customer.set_password("userpass123")

        db.session.add_all([admin, customer])
        db.session.commit()
        print("Default Admin and Customer profiles seeded.")
