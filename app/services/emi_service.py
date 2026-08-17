from decimal import Decimal, ROUND_HALF_UP

class EMIService:
    @staticmethod
    def calculate_emi(principal, annual_rate, tenure_months):
        """
        Calculates monthly EMI, total payable, and interest using Decimal math.
        Gracefully handles zero-interest promotions.
        """
        P = Decimal(str(principal))
        rate_annual = Decimal(str(annual_rate))
        n = int(tenure_months)

        if P <= 0 or rate_annual < 0 or n <= 0:
            raise ValueError("Principal, rate, and tenure must be positive values.")

        if rate_annual == 0:
            emi = (P / Decimal(n)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            total_payable = emi * Decimal(n)
            total_interest = Decimal('0.00')
        else:
            r = rate_annual / Decimal('100') / Decimal('12')
            power = (1 + r) ** n
            raw_emi = P * r * power / (power - 1)
            emi = raw_emi.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            total_payable = emi * Decimal(n)
            total_interest = total_payable - P

        total_payable = total_payable.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        total_interest = total_interest.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        return {
            'monthly_emi': emi,
            'total_payable': total_payable,
            'total_interest': total_interest,
            'principal': P
        }

    @staticmethod
    def generate_amortization_schedule(principal, annual_rate, tenure_months):
        """
        Generates the month-by-month principal and interest breakdown.
        """
        P = Decimal(str(principal))
        rate_annual = Decimal(str(annual_rate))
        n = int(tenure_months)

        summary = EMIService.calculate_emi(P, rate_annual, n)
        emi = summary['monthly_emi']

        schedule = []
        balance = P

        if rate_annual == 0:
            monthly_principal = (P / Decimal(n)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            for i in range(1, n + 1):
                if i == n:
                    monthly_principal = balance
                    balance = Decimal('0.00')
                else:
                    balance -= monthly_principal
                schedule.append({
                    'month': i,
                    'emi': monthly_principal,
                    'principal_paid': monthly_principal,
                    'interest_paid': Decimal('0.00'),
                    'balance_remaining': balance
                })
        else:
            r = rate_annual / Decimal('100') / Decimal('12')
            for i in range(1, n + 1):
                interest = (balance * r).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                principal_paid = emi - interest

                if i == n:
                    principal_paid = balance
                    balance = Decimal('0.00')
                else:
                    balance -= principal_paid

                schedule.append({
                    'month': i,
                    'emi': emi,
                    'principal_paid': principal_paid.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                    'interest_paid': interest,
                    'balance_remaining': max(Decimal('0.00'), balance).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                })

        return schedule
