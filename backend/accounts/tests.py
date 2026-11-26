import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from accounts.models import Society
from complaints.models import Category

User = get_user_model()

@pytest.fixture
def society(db):
    return Society.objects.create(name='Maple Residency', address='12 Main Road', contact_information='office@example.test')

@pytest.fixture
def resident(db, society):
    return User.objects.create_user(username='resident1', email='resident@example.test', password='StrongPass!123', role='resident', society=society)

@pytest.fixture
def manager(db, society):
    return User.objects.create_user(username='manager1', email='manager@example.test', password='StrongPass!123', role='manager', society=society)

@pytest.fixture
def worker(db, society):
    return User.objects.create_user(username='worker1', email='worker@example.test', password='StrongPass!123', role='worker', society=society)

@pytest.fixture
def other_society(db):
    return Society.objects.create(name='Pine Residency', address='22 Hill Road', contact_information='pine@example.test')

@pytest.fixture
def category(db):
    return Category.objects.create(name='Plumbing', description='Leaks and water supply')

@pytest.fixture
def auth_client():
    return APIClient()

@pytest.mark.django_db
def test_public_registration_always_creates_resident(auth_client, society):
    response = auth_client.post('/api/auth/register/', {'username':'newhome','email':'new@example.test','society':society.id,'role':'manager','password':'StrongPass!123','password_confirm':'StrongPass!123'}, format='json')
    assert response.status_code == 201
    assert response.data['user']['role'] == 'resident'

@pytest.mark.django_db
def test_resident_login(auth_client, resident):
    response = auth_client.post('/api/auth/login/', {'email':resident.email,'password':'StrongPass!123'}, format='json')
    assert response.status_code == 200
    assert response.data['access']
    assert response.data['refresh']

@pytest.mark.django_db
def test_manager_and_worker_login(auth_client, manager, worker):
    for account in [manager, worker]:
        response = auth_client.post('/api/auth/login/', {'email':account.email,'password':'StrongPass!123'}, format='json')
        assert response.status_code == 200
        assert response.data['access']
