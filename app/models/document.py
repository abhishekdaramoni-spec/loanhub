from datetime import datetime
from app.utils.extensions import db

class Document(db.Model):
    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    loan_application_id = db.Column(db.Integer, db.ForeignKey('loan_applications.id'), nullable=True)
    doc_type = db.Column(db.String(50), nullable=False) # 'PAN', 'Aadhar', 'Salary Slip', 'Bank Statement', 'Other'
    filename = db.Column(db.String(255), nullable=False, unique=True)
    original_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=False) # file size in bytes
    mime_type = db.Column(db.String(100), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Document ID {self.id} type {self.doc_type} name {self.filename}>"
