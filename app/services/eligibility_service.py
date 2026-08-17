from decimal import Decimal
from datetime import datetime

class EligibilityService:
    @staticmethod
    def assess_eligibility(loan_type, dob, monthly_income, requested_amount, tenure_months, existing_liabilities=0):
        """
        Demo Credit Eligibility Assessment Engine.
        Validates age bounds, income thresholds, debt-to-income limits (FOIR), and loan specifications.
        """
        income = Decimal(str(monthly_income))
        amount = Decimal(str(requested_amount))
        liabilities = Decimal(str(existing_liabilities))
        tenure = int(tenure_months)

        # Determine age
        if isinstance(dob, str):
            dob_date = datetime.strptime(dob, '%Y-%m-%d').date()
        else:
            dob_date = dob

        today = datetime.utcnow().date()
        age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))

        # 1. Validate Age Restrictions
        if age < 21:
            return {
                'eligible': False,
                'reason': "Applicant must be at least 21 years old.",
                'score': 20,
                'recommended_amount': Decimal('0.00'),
                'recommended_tenure': 0
            }
        if age > 65:
            return {
                'eligible': False,
                'reason': "Applicant's age exceeds maximum limit of 65 years.",
                'score': 30,
                'recommended_amount': Decimal('0.00'),
                'recommended_tenure': 0
            }

        # 2. Validate Income Thresholds
        if income < Decimal('15000.00'):
            return {
                'eligible': False,
                'reason': "Minimum monthly income threshold of INR 15,000 not met.",
                'score': 40,
                'recommended_amount': Decimal('0.00'),
                'recommended_tenure': 0
            }

        # 3. Check requested amounts against loan limits
        if amount < loan_type.min_amount:
            return {
                'eligible': False,
                'reason': f"Requested amount is below minimum limit of INR {loan_type.min_amount:,.2f} for this loan scheme.",
                'score': 45,
                'recommended_amount': loan_type.min_amount,
                'recommended_tenure': tenure
            }
        if amount > loan_type.max_amount:
            return {
                'eligible': False,
                'reason': f"Requested amount exceeds maximum limit of INR {loan_type.max_amount:,.2f} for this loan scheme.",
                'score': 50,
                'recommended_amount': loan_type.max_amount,
                'recommended_tenure': tenure
            }

        # 4. Check Debt-to-Income (FOIR) limits
        rate_annual = loan_type.min_interest_rate

        # Calculate expected monthly obligation
        if rate_annual == 0:
            expected_emi = amount / Decimal(tenure)
        else:
            r = rate_annual / Decimal('100') / Decimal('12')
            power = (1 + r) ** tenure
            expected_emi = amount * r * power / (power - 1)

        total_monthly_obligations = liabilities + expected_emi
        foir = (total_monthly_obligations / income) * 100

        # Maximum allowed FOIR is 55%
        if foir > Decimal('55.00'):
            max_allowed_emi = (income * Decimal('0.5')) - liabilities
            if max_allowed_emi <= 0:
                return {
                    'eligible': False,
                    'reason': "Existing liabilities exceed 50% of monthly income.",
                    'score': 35,
                    'recommended_amount': Decimal('0.00'),
                    'recommended_tenure': 0
                }

            # Estimate recommended loan amount matching the 50% FOIR limit
            if rate_annual == 0:
                rec_amount = max_allowed_emi * Decimal(tenure)
            else:
                r = rate_annual / Decimal('100') / Decimal('12')
                power = (1 + r) ** tenure
                rec_amount = max_allowed_emi * (power - 1) / (r * power)

            rec_amount = min(rec_amount, loan_type.max_amount)
            rec_amount = max(rec_amount, loan_type.min_amount)

            return {
                'eligible': False,
                'reason': f"Estimated Debt-to-Income Ratio ({foir:.1f}%) exceeds policy guideline limit of 55%.",
                'score': 55,
                'recommended_amount': rec_amount.quantize(Decimal('100.00')),
                'recommended_tenure': tenure
            }

        # Calculate credit assessment score
        score = 80
        if foir < Decimal('30.00'):
            score += 15
        if income > Decimal('60000.00'):
            score += 5

        return {
            'eligible': True,
            'reason': "Financial obligations, age, and income meet standard underwriting guidelines.",
            'score': min(100, score),
            'recommended_amount': amount,
            'recommended_tenure': tenure
        }

    @staticmethod
    def assess_general_limit(income, credit_score, existing_emi):
        """
        Calculates credit limits based on debt capacity and credit scores.
        """
        inc = Decimal(str(income))
        existing = Decimal(str(existing_emi))
        score = int(credit_score)

        if score < 600:
            return {
                'eligible': False,
                'reason': 'Minimum Credit Score of 600 required.'
            }

        foir_limit = inc * Decimal('0.5')
        max_allowed_emi = foir_limit - existing

        if max_allowed_emi <= 0:
            return {
                'eligible': False,
                'reason': 'Your current EMI obligations exceed 50% of your income. Eligibility limit reached.'
            }

        rate_annual = Decimal('10.00')
        if score >= 750:
            rate_annual = Decimal('8.50')
        elif score >= 700:
            rate_annual = Decimal('9.50')
        else:
            rate_annual = Decimal('11.50')

        r = rate_annual / Decimal('100') / Decimal('12')
        n = 60
        power = (1 + r) ** n
        max_loan_amount = max_allowed_emi * (power - 1) / (r * power)

        return {
            'eligible': True,
            'max_loan_amount': max_loan_amount,
            'max_emi': max_allowed_emi,
            'interest_rate_offered': rate_annual
        }
