from datetime import datetime
from app.utils.extensions import db

class LoanType(db.Model):
    __tablename__ = 'loan_types'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False) # e.g. Retail, Commercial, Agriculture, Special
    min_amount = db.Column(db.Numeric(15, 2), nullable=False)
    max_amount = db.Column(db.Numeric(15, 2), nullable=False)
    min_interest_rate = db.Column(db.Numeric(5, 2), nullable=False)
    max_interest_rate = db.Column(db.Numeric(5, 2), nullable=False)
    processing_fee_pct = db.Column(db.Numeric(4, 2), nullable=False)
    min_tenure_months = db.Column(db.Integer, nullable=False)
    max_tenure_months = db.Column(db.Integer, nullable=False)
    eligibility_criteria = db.Column(db.Text, nullable=False)
    approval_time = db.Column(db.String(50), nullable=False) # e.g. "24 Hours", "3 Working Days"
    icon_class = db.Column(db.String(50), nullable=False, default='fa-wallet')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    applications = db.relationship('LoanApplication', backref='loan_type', lazy=True)
    rates = db.relationship('InterestRate', backref='loan_type', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<LoanType {self.name}>"


class LoanApplication(db.Model):
    __tablename__ = 'loan_applications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    loan_type_id = db.Column(db.Integer, db.ForeignKey('loan_types.id'), nullable=False)

    # Form details
    full_name = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text, nullable=False)
    occupation = db.Column(db.String(100), nullable=False)
    employer = db.Column(db.String(100), nullable=False)
    monthly_income = db.Column(db.Numeric(15, 2), nullable=False)
    loan_amount = db.Column(db.Numeric(15, 2), nullable=False)
    tenure_months = db.Column(db.Integer, nullable=False)
    pan_number = db.Column(db.String(20), nullable=False)
    aadhar_number = db.Column(db.String(20), nullable=False)

    # Uploaded docs (filenames)
    pan_doc = db.Column(db.String(255), nullable=False)
    aadhar_doc = db.Column(db.String(255), nullable=False)
    salary_slip_doc = db.Column(db.String(255), nullable=False)
    bank_statement_doc = db.Column(db.String(255), nullable=False)

    # Approval status
    status = db.Column(db.String(30), nullable=False, default='Pending') # Pending, In Review, Approved, Rejected
    remarks = db.Column(db.Text, nullable=True)
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    emi_payments = db.relationship('EMIHistory', backref='application', lazy=True, cascade="all, delete-orphan")
    status_history = db.relationship('LoanStatusHistory', backref='application', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<LoanApplication ID {self.id} for User {self.user_id}>"


class LoanStatusHistory(db.Model):
    __tablename__ = 'loan_status_history'

    id = db.Column(db.Integer, primary_key=True)
    loan_application_id = db.Column(db.Integer, db.ForeignKey('loan_applications.id'), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    remarks = db.Column(db.Text, nullable=True)
    changed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    changed_by = db.relationship('User', foreign_keys=[changed_by_id])

    def __repr__(self):
        return f"<LoanStatusHistory ID {self.id} Application {self.loan_application_id} Status {self.status}>"
