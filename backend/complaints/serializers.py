from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from accounts.models import Society, User
from .models import Category, Complaint, ComplaintHistory


class SocietySerializer(serializers.ModelSerializer):
    class Meta:
        model = Society
        fields = ('id', 'name', 'address', 'contact_information')


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'description')


class HistorySerializer(serializers.ModelSerializer):
    updated_by_name = serializers.CharField(
        source='updated_by.username', read_only=True, allow_null=True,
    )

    class Meta:
        model = ComplaintHistory
        fields = (
            'id', 'previous_status', 'new_status', 'updated_by_name',
            'remarks', 'created_at',
        )


class ComplaintSerializer(serializers.ModelSerializer):
    upvotes = serializers.IntegerField(source='votes.count', read_only=True)
    history = HistorySerializer(many=True, read_only=True)
    reported_by_name = serializers.CharField(source='reported_by.username', read_only=True)
    assigned_to_name = serializers.CharField(
        source='assigned_to.username', read_only=True, allow_null=True,
    )
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Complaint
        fields = (
            'id', 'title', 'description', 'category', 'category_name',
            'severity', 'priority', 'status', 'image', 'society',
            'reported_by', 'reported_by_name', 'assigned_to', 'assigned_to_name',
            'upvotes', 'history', 'created_at', 'updated_at',
        )
        read_only_fields = (
            'priority', 'status', 'society', 'reported_by', 'assigned_to',
        )

    def validate_title(self, value):
        title = value.strip()
        if not title:
            raise serializers.ValidationError('Title cannot be blank.')
        return title

    def validate_description(self, value):
        description = value.strip()
        if not description:
            raise serializers.ValidationError('Description cannot be blank.')
        if len(description) > 4000:
            raise serializers.ValidationError('Description must be 4,000 characters or fewer.')
        return description


class WorkerSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'role', 'society')
        read_only_fields = ('role', 'society')

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value.strip()).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value.strip().lower()

    def validate_username(self, value):
        username = value.strip()
        if User.objects.filter(username__iexact=username).exists():
            raise serializers.ValidationError('A user with that username already exists.')
        return username

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        return value

    def create(self, validated_data):
        manager = self.context['request'].user
        return User.objects.create_user(
            **validated_data,
            role='worker',
            society=manager.society,
        )
