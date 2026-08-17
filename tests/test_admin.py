import pytest
from app.models.user import User
from app.utils.extensions import db

def test_admin_dashboard_restricted(client, app):
    """Verify that non-admin users receive a 403 Forbidden on admin paths."""
    with app.app_context():
        user = User(name='Customer User', email='customer@example.com', phone='9876543210')
        user.set_password('Password123!')
        db.session.add(user)
        db.session.commit()
        
    client.post('/auth/login', data={
        'email': 'customer@example.com',
        'password': 'Password123!'
    })
    
    # Non-admin access check
    response = client.get('/admin/')
    assert response.status_code == 403

def test_admin_dashboard_allowed(client, app):
    """Verify that admins are permitted access to the admin dashboard."""
    with app.app_context():
        user = User(name='Admin User', email='admin@example.com', is_admin=True, phone='9876543212')
        user.set_password('Password123!')
        db.session.add(user)
        db.session.commit()
        
    client.post('/auth/login', data={
        'email': 'admin@example.com',
        'password': 'Password123!'
    })
    
    # Admin access check
    response = client.get('/admin/')
    assert response.status_code == 200
