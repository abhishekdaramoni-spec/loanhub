from datetime import datetime
from app.utils.extensions import db

class InterestRate(db.Model):
    __tablename__ = 'interest_rates'

    id = db.Column(db.Integer, primary_key=True)
    loan_type_id = db.Column(db.Integer, db.ForeignKey('loan_types.id'), nullable=False)
    tenure_months = db.Column(db.Integer, nullable=False)
    rate_pct = db.Column(db.Numeric(5, 2), nullable=False)
    effective_from = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    status = db.Column(db.String(20), nullable=False, default='Active') # Active, Inactive

    def __repr__(self):
        return f"<InterestRate {self.rate_pct}% for LoanType ID {self.loan_type_id}>"
