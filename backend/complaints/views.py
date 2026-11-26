from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Society, User
from .models import Category, Complaint, ComplaintHistory, ComplaintVote
from .permissions import SocietyRolePermission
from .serializers import (
    CategorySerializer,
    ComplaintSerializer,
    SocietySerializer,
    WorkerSerializer,
)


def calculate_priority(severity, upvotes, age_days):
    """Score impact, resident interest, and wait time with a small rule set."""
    score = {'low': 1, 'medium': 2, 'high': 3, 'critical': 5}.get(severity, 2)
    score += min(upvotes // 3, 3) + min(age_days // 7, 2)
    if score >= 7:
        return 'urgent'
    if score >= 5:
        return 'high'
    if score >= 3:
        return 'medium'
    return 'low'


class SocietyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Society.objects.all().order_by('name')
    serializer_class = SocietySerializer
    permission_classes = [AllowAny]


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]


class ComplaintViewSet(viewsets.ModelViewSet):
    serializer_class = ComplaintSerializer
    permission_classes = [IsAuthenticated, SocietyRolePermission]

    def get_queryset(self):
        user = self.request.user
        queryset = Complaint.objects.filter(
            society_id=user.society_id,
        ).select_related(
            'category', 'society', 'reported_by', 'assigned_to',
        )
        if user.role == 'worker':
            queryset = queryset.filter(assigned_to=user)
        return queryset

    @transaction.atomic
    def perform_create(self, serializer):
        user = self.request.user
        if user.role != 'resident' or not user.society_id:
            raise PermissionDenied('Only residents with a society can report complaints.')
        complaint = serializer.save(society=user.society, reported_by=user)
        complaint.priority = calculate_priority(complaint.severity, 0, 0)
        complaint.save(update_fields=['priority'])
        ComplaintHistory.objects.create(
            complaint=complaint,
            previous_status='',
            new_status='open',
            updated_by=user,
            remarks='Complaint reported',
        )

    def create(self, request, *args, **kwargs):
        if request.user.role != 'resident':
            raise PermissionDenied('Only residents can create complaints.')
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        raise PermissionDenied('Complaint details are not editable.')

    partial_update = update

    def destroy(self, request, *args, **kwargs):
        raise PermissionDenied('Complaints cannot be deleted.')

    @action(detail=True, methods=['post'])
    def upvote(self, request, pk=None):
        if request.user.role != 'resident':
            raise PermissionDenied('Only residents can upvote.')
        complaint = self.get_object()
        ComplaintVote.objects.get_or_create(complaint=complaint, user=request.user)
        age_days = (timezone.now() - complaint.created_at).days
        complaint.priority = calculate_priority(
            complaint.severity,
            complaint.votes.count(),
            age_days,
        )
        complaint.save(update_fields=['priority'])
        return Response(self.get_serializer(complaint).data)

    @action(detail=True, methods=['patch'])
    @transaction.atomic
    def assign(self, request, pk=None):
        if request.user.role != 'manager':
            raise PermissionDenied('Only managers can assign workers.')
        if not isinstance(request.data, dict):
            raise ValidationError({'error': 'Expected a JSON object.'})

        complaint = self.get_object()
        worker_id = request.data.get('assigned_to')
        worker = User.objects.filter(
            pk=worker_id,
            society=request.user.society,
            role='worker',
            is_active=True,
        ).first() if worker_id else None
        if worker is None:
            raise ValidationError({'assigned_to': 'Choose an active worker in your society.'})

        previous_status = complaint.status
        complaint.assigned_to = worker
        if complaint.status == 'open':
            complaint.status = 'assigned'
        complaint.save()
        if complaint.status != previous_status:
            ComplaintHistory.objects.create(
                complaint=complaint,
                previous_status=previous_status,
                new_status=complaint.status,
                updated_by=request.user,
                remarks=f'Assigned to {worker.username}',
            )
        return Response(self.get_serializer(complaint).data)

    @action(detail=True, methods=['patch'])
    def priority(self, request, pk=None):
        if request.user.role != 'manager':
            raise PermissionDenied('Only managers can change priority.')
        if not isinstance(request.data, dict):
            raise ValidationError({'error': 'Expected a JSON object.'})

        complaint = self.get_object()
        value = request.data.get('priority')
        choices = {choice for choice, _label in Complaint.PRIORITY_CHOICES}
        if value not in choices:
            raise ValidationError({'priority': 'Choose low, medium, high, or urgent.'})
        complaint.priority = value
        complaint.save(update_fields=['priority', 'updated_at'])
        return Response(self.get_serializer(complaint).data)

    @action(detail=True, methods=['patch'])
    @transaction.atomic
    def status(self, request, pk=None):
        if not isinstance(request.data, dict):
            raise ValidationError({'error': 'Expected a JSON object.'})

        complaint = self.get_object()
        target_status = request.data.get('status')
        remarks = str(request.data.get('remarks', ''))[:500]
        role = request.user.role
        allowed_statuses = {
            'manager': {'in_progress', 'resolved'},
            'worker': {'in_progress', 'resolved'},
            'resident': {'verified', 'open'},
        }
        if target_status not in allowed_statuses.get(role, set()):
            raise PermissionDenied('This role cannot set that complaint status.')
        if role == 'worker' and complaint.assigned_to_id != request.user.id:
            raise PermissionDenied('Workers can update only complaints assigned to them.')
        if role == 'resident' and (
            complaint.reported_by_id != request.user.id
            or complaint.status != 'resolved'
        ):
            raise PermissionDenied('You can verify or reopen only your resolved complaints.')

        transitions = {
            'open': {'assigned'},
            'assigned': {'in_progress'},
            'in_progress': {'resolved'},
            'resolved': {'verified', 'open'},
            'verified': set(),
        }
        if target_status not in transitions.get(complaint.status, set()):
            raise ValidationError({
                'status': f'Cannot move from {complaint.status} to {target_status}.'
            })

        previous_status = complaint.status
        complaint.status = target_status
        update_fields = ['status', 'updated_at']
        if target_status == 'open':
            complaint.assigned_to = None
            update_fields.append('assigned_to')
        complaint.save(update_fields=update_fields)
        ComplaintHistory.objects.create(
            complaint=complaint,
            previous_status=previous_status,
            new_status=target_status,
            updated_by=request.user,
            remarks=remarks,
        )
        return Response(self.get_serializer(complaint).data)


class WorkerViewSet(viewsets.ModelViewSet):
    serializer_class = WorkerSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        if self.request.user.role != 'manager':
            raise PermissionDenied('Managers only.')
        return User.objects.filter(
            role='worker', society=self.request.user.society,
        ).order_by('username')

    def create(self, request, *args, **kwargs):
        if request.user.role != 'manager' or not request.user.society_id:
            raise PermissionDenied('Managers with a society only.')
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        worker = serializer.save()
        return Response(self.get_serializer(worker).data, status=status.HTTP_201_CREATED)


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = Complaint.objects.filter(society=request.user.society)
        if request.user.role == 'worker':
            queryset = queryset.filter(assigned_to=request.user)
        return Response({
            'total': queryset.count(),
            'open': queryset.filter(status__in=['open', 'assigned']).count(),
            'in_progress': queryset.filter(status='in_progress').count(),
            'resolved': queryset.filter(status__in=['resolved', 'verified']).count(),
        })
