import pytest
from datetime import datetime
from app.models.loan import LoanApplication, LoanType
from app.models.user import User
from app.services.loan_service import LoanService
from app.utils.extensions import db

def test_loan_state_machine_transitions(app):
    """Test standard state machine transitions and audit log insertions."""
    with app.app_context():
        user = User(name='Applicant', email='applicant@example.com', phone='9000000000')
        user.set_password('Password123!')
        db.session.add(user)
        db.session.commit()
        
        loan_type = LoanType.query.first()
        
        # Create a new loan application in 'Pending' state
        app_record = LoanApplication(
            user_id=user.id,
            loan_type_id=loan_type.id,
            full_name='Applicant Name',
            dob=datetime.strptime('1995-05-15', '%Y-%m-%d').date(),
            gender='Male',
            email='applicant@example.com',
            phone='9000000000',
            address='123 Road',
            occupation='Salaried',
            employer='Corp',
            monthly_income=50000,
            loan_amount=100000,
            tenure_months=24,
            pan_number='ABCDE1234F',
            aadhar_number='123456789012',
            pan_doc='pan.pdf',
            aadhar_doc='aadhar.pdf',
            salary_slip_doc='salary.pdf',
            bank_statement_doc='bank.pdf',
            status='Pending'
        )
        db.session.add(app_record)
        db.session.commit()
        
        # Pending (SUBMITTED) -> In Review (UNDER_REVIEW) is allowed
        history = LoanService.transition_status(app_record, 'In Review', user, 'Verifying documents.')
        assert app_record.status == 'In Review'
        assert history.status == 'In Review'
        assert len(app_record.status_history) == 1
        
        # Closed -> Pending should be forbidden
        app_record.status = 'Closed'
        db.session.commit()
        
        with pytest.raises(ValueError):
            LoanService.transition_status(app_record, 'Pending', user)
