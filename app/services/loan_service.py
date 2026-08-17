from app.utils.extensions import db
from app.models.loan import LoanStatusHistory

# Map of allowed status transitions (State Machine lifecycle)
TRANSITION_RULES = {
    'DRAFT': ['SUBMITTED'],
    'SUBMITTED': ['UNDER_REVIEW', 'APPROVED', 'REJECTED'],
    'UNDER_REVIEW': ['DOCUMENT_VERIFICATION', 'APPROVED', 'REJECTED'],
    'DOCUMENT_VERIFICATION': ['ELIGIBILITY_CHECK', 'APPROVED', 'REJECTED'],
    'ELIGIBILITY_CHECK': ['APPROVED', 'REJECTED'],
    'APPROVED': ['SANCTIONED', 'REJECTED'],
    'SANCTIONED': ['DISBURSED', 'REJECTED'],
    'DISBURSED': ['ACTIVE'],
    'ACTIVE': ['REPAYMENT'],
    'REPAYMENT': ['CLOSED'],
    'REJECTED': ['SUBMITTED']
}

class LoanService:
    @staticmethod
    def transition_status(application, new_status, user, remarks=None):
        """
        Enforces state machine transitions on a loan application.
        Logs every transition in the LoanStatusHistory table.
        """
        old_status = application.status.upper() if application.status else 'SUBMITTED'
        target_status = new_status.upper()

        # Map display statuses to standard state machine codes for compatibility
        if old_status == 'PENDING':
            old_status = 'SUBMITTED'
        if target_status == 'PENDING':
            target_status = 'SUBMITTED'

        if old_status == 'IN REVIEW':
            old_status = 'UNDER_REVIEW'
        if target_status == 'IN REVIEW':
            target_status = 'UNDER_REVIEW'

        # Check if the transition path is allowed
        allowed_targets = TRANSITION_RULES.get(old_status, [])
        if target_status not in allowed_targets:
            raise ValueError(f"Invalid state transition from '{application.status}' to '{new_status}'.")

        # Set new status
        application.status = new_status
        application.remarks = remarks

        # Log transition details in the history table
        history = LoanStatusHistory(
            loan_application_id=application.id,
            status=new_status,
            remarks=remarks,
            changed_by_id=user.id if user else None
        )
        db.session.add(history)
        db.session.commit()
        return history
