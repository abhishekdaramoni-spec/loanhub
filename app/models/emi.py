from datetime import datetime
from app.utils.extensions import db

class EMIHistory(db.Model):
    __tablename__ = 'emi_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    loan_application_id = db.Column(db.Integer, db.ForeignKey('loan_applications.id'), nullable=False)
    amount_paid = db.Column(db.Numeric(15, 2), nullable=False)
    principal_paid = db.Column(db.Numeric(15, 2), nullable=False)
    interest_paid = db.Column(db.Numeric(15, 2), nullable=False)
    balance_remaining = db.Column(db.Numeric(15, 2), nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='Paid') # Paid, Overdue, Failed

    def __repr__(self):
        return f"<EMIHistory ID {self.id} Application {self.loan_application_id}>"
