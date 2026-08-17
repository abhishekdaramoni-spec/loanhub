from datetime import datetime
from app.utils.extensions import db

class Repayment(db.Model):
    __tablename__ = 'repayments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    loan_application_id = db.Column(db.Integer, db.ForeignKey('loan_applications.id'), nullable=False)
    transaction_id = db.Column(db.String(100), unique=True, nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False) # e.g. 'UPI', 'NetBanking', 'Card'
    payment_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(30), nullable=False, default='Completed') # 'Completed', 'Failed', 'Pending'

    def __repr__(self):
        return f"<Repayment Transaction {self.transaction_id} Amount {self.amount}>"
