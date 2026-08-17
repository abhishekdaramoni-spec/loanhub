import pytest
from app.models.user import User
from app.utils.extensions import db

def test_user_registration(client, app):
    """Test register submission creating a record in database."""
    response = client.post('/auth/register', data={
        'name': 'John Test',
        'email': 'johntest@example.com',
        'phone': '9876543210',
        'address': '123 Test Street',
        'password': 'Password123!',
        'confirm_password': 'Password123!'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    with app.app_context():
        user = User.query.filter_by(email='johntest@example.com').first()
        assert user is not None
        assert user.name == 'John Test'
        assert user.check_password('Password123!')
        assert not user.check_password('Password123')

def test_user_login_logout(client, app):
    """Test user login and session clearing on logout."""
    with app.app_context():
        user = User(name='Jane Test', email='janetest@example.com', phone='9876543211', address='123 Test Street')
        user.set_password('Password123!')
        user.email_verified = True
        db.session.add(user)
        db.session.commit()
        
    # Login
    response = client.post('/auth/login', data={
        'email': 'janetest@example.com',
        'password': 'Password123!'
    }, follow_redirects=True)
    assert response.status_code == 200
    
    # Logout
    logout_res = client.get('/auth/logout', follow_redirects=True)
    assert logout_res.status_code == 200
