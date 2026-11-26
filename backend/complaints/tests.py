import pytest
from rest_framework.test import APIClient
from accounts.models import Society
from complaints.models import Complaint, ComplaintHistory
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.fixture
def signed_in():
    return APIClient()

def login(client, user):
    from rest_framework_simplejwt.tokens import RefreshToken
    token = str(RefreshToken.for_user(user).access_token)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return client

@pytest.fixture
def setup_people(db):
    society = Society.objects.create(name='Cedar Homes', address='1 Park Ave', contact_information='care@cedar.test')
    other = Society.objects.create(name='Birch Homes', address='2 Park Ave', contact_information='care@birch.test')
    resident = User.objects.create_user(username='asha', email='asha@example.test', password='StrongPass!123', role='resident', society=society)
    neighbor = User.objects.create_user(username='dev', email='dev@example.test', password='StrongPass!123', role='resident', society=society)
    manager = User.objects.create_user(username='mira', email='mira@example.test', password='StrongPass!123', role='manager', society=society)
    worker = User.objects.create_user(username='raj', email='raj@example.test', password='StrongPass!123', role='worker', society=society)
    outsider = User.objects.create_user(username='lee', email='lee@example.test', password='StrongPass!123', role='resident', society=other)
    from complaints.models import Category
    category = Category.objects.create(name='Water')
    complaint = Complaint.objects.create(title='Leaking pipe', description='Pipe leaking on floor 2', category=category, society=society, reported_by=resident, severity='high')
    return locals()

@pytest.mark.django_db
def test_complaint_creation_and_history(signed_in, setup_people):
    p=setup_people; login(signed_in,p['resident'])
    response=signed_in.post('/api/complaints/', {'title':'Lift stalled','description':'Lift 1 stopped','category':p['category'].id,'severity':'critical'}, format='json')
    assert response.status_code == 201
    assert response.data['society'] == p['society'].id
    assert response.data['reported_by'] == p['resident'].id
    assert response.data['history'][0]['new_status'] == 'open'

@pytest.mark.django_db
def test_vote_is_unique_and_updates_priority(signed_in, setup_people):
    p=setup_people; login(signed_in,p['neighbor'])
    for _ in range(2): response=signed_in.post(f"/api/complaints/{p['complaint'].id}/upvote/")
    assert response.status_code == 200
    assert p['complaint'].votes.count() == 1

@pytest.mark.django_db
def test_manager_creates_worker_and_assigns(signed_in, setup_people):
    p=setup_people; login(signed_in,p['manager'])
    created=signed_in.post('/api/workers/', {'username':'newtech','email':'tech@example.test','password':'StrongPass!123'}, format='json')
    assert created.status_code == 201
    response=signed_in.patch(f"/api/complaints/{p['complaint'].id}/assign/", {'assigned_to':p['worker'].id}, format='json')
    assert response.status_code == 200 and response.data['status'] == 'assigned'

@pytest.mark.django_db
def test_manager_cannot_assign_worker_from_another_society(signed_in, setup_people):
    p = setup_people
    external_worker = User.objects.create_user(
        username='othertech', email='othertech@example.test', password='StrongPass!123',
        role='worker', society=p['other'],
    )
    login(signed_in, p['manager'])
    response = signed_in.patch(
        f"/api/complaints/{p['complaint'].id}/assign/",
        {'assigned_to': external_worker.id}, format='json',
    )
    assert response.status_code == 400

@pytest.mark.django_db
def test_manager_can_change_priority(signed_in, setup_people):
    p = setup_people
    login(signed_in, p['manager'])
    response = signed_in.patch(
        f"/api/complaints/{p['complaint'].id}/priority/",
        {'priority': 'urgent'}, format='json',
    )
    assert response.status_code == 200
    assert response.data['priority'] == 'urgent'

@pytest.mark.django_db
def test_worker_status_and_resident_verification(signed_in, setup_people):
    p=setup_people; c=p['complaint']; c.assigned_to=p['worker']; c.status='assigned'; c.save()
    login(signed_in,p['worker'])
    assert signed_in.patch(f'/api/complaints/{c.id}/status/', {'status':'in_progress'}, format='json').status_code == 200
    assert signed_in.patch(f'/api/complaints/{c.id}/status/', {'status':'resolved'}, format='json').status_code == 200
    login(signed_in,p['resident'])
    response=signed_in.patch(f'/api/complaints/{c.id}/status/', {'status':'verified'}, format='json')
    assert response.status_code == 200 and response.data['status'] == 'verified'
    assert c.history.count() == 3

@pytest.mark.django_db
def test_worker_can_only_update_assigned_work(signed_in, setup_people):
    p=setup_people; login(signed_in,p['worker'])
    response=signed_in.patch(f"/api/complaints/{p['complaint'].id}/status/", {'status':'in_progress'}, format='json')
    assert response.status_code == 404

@pytest.mark.django_db
def test_society_records_are_isolated(signed_in, setup_people):
    p=setup_people; login(signed_in,p['outsider'])
    assert signed_in.get(f"/api/complaints/{p['complaint'].id}/").status_code == 404
    assert signed_in.get('/api/complaints/').data['count'] == 0

@pytest.mark.django_db
def test_residents_cannot_assign_or_set_admin_status(signed_in, setup_people):
    p=setup_people; login(signed_in,p['resident']); c=p['complaint']
    assert signed_in.patch(f'/api/complaints/{c.id}/assign/', {'assigned_to':p['worker'].id}, format='json').status_code == 403
    assert signed_in.patch(f'/api/complaints/{c.id}/status/', {'status':'resolved'}, format='json').status_code == 403
    assert signed_in.patch(f'/api/complaints/{c.id}/', {'status':'resolved'}, format='json').status_code == 403

@pytest.mark.django_db
def test_resolved_complaint_can_be_reopened(signed_in, setup_people):
    p=setup_people; c=p['complaint']; c.status='resolved'; c.save(update_fields=['status'])
    login(signed_in,p['resident'])
    response=signed_in.patch(f'/api/complaints/{c.id}/status/', {'status':'open','remarks':'Still leaking'}, format='json')
    assert response.status_code == 200 and response.data['status'] == 'open'
