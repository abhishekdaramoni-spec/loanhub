import pytest

def test_health_check_endpoint(client):
    """Test that the health check endpoint returns 200 and indicates healthy status."""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert data['database'] == 'connected'
