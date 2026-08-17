import pytest
from io import BytesIO
from werkzeug.datastructures import FileStorage
from app.models.user import User
from app.models.document import Document
from app.utils.validators import validate_file_security
from app.utils.extensions import db

def test_file_upload_security():
    """Verify that dangerous file extensions are rejected."""
    file_exe = FileStorage(stream=BytesIO(b"exe payload"), filename="hack.exe")
    is_secure, res = validate_file_security(file_exe, {'pdf', 'png'}, 1024)
    assert not is_secure
    assert "Unsupported file type" in res

def test_file_upload_size_limit():
    """Verify that file size limits are enforced."""
    file_large = FileStorage(stream=BytesIO(b"x" * 2000), filename="large.pdf")
    is_secure, res = validate_file_security(file_large, {'pdf'}, 1000)
    assert not is_secure
    assert "exceeds maximum allowed limit" in res

def test_document_download_isolation(client, app):
    """Verify that users cannot download other users' uploaded documents."""
    with app.app_context():
        user1 = User(name='User One', email='user1@example.com', phone='9000000001')
        user1.set_password('Password123!')
        user2 = User(name='User Two', email='user2@example.com', phone='9000000002')
        user2.set_password('Password123!')
        
        db.session.add_all([user1, user2])
        db.session.commit()
        
        doc = Document(
            user_id=user1.id,
            doc_type='PAN',
            filename='unique_pan.pdf',
            original_filename='my_pan.pdf',
            file_size=120,
            mime_type='application/pdf'
        )
        db.session.add(doc)
        db.session.commit()
        
    # Authenticate as user2
    client.post('/auth/login', data={
        'email': 'user2@example.com',
        'password': 'Password123!'
    })
    
    # Attempt to download user1's document
    response = client.get('/loans/document/unique_pan.pdf')
    assert response.status_code == 403
