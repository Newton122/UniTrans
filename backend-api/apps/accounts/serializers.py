from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from apps.notifications.services import notify_driver_manager_update

from .driver_bus import validate_driver_assigned_bus
from .models import Driver, Student, User
from .phone_utils import normalize_phone


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['user_id', 'name', 'email', 'role', 'is_active', 'date_joined']
        read_only_fields = ['user_id', 'date_joined']


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = [
            'student_id', 'registration_number', 'first_name',
            'last_name', 'email', 'phone',
        ]
        read_only_fields = ['student_id']


class StudentDetailSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Student
        fields = [
            'student_id', 'registration_number', 'first_name',
            'last_name', 'email', 'phone', 'password', 'user',
        ]
        read_only_fields = ['student_id']


class RegisterSerializer(serializers.Serializer):
    registration_number = serializers.CharField(max_length=50)
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        if Student.objects.filter(email=value).exists():
            raise serializers.ValidationError('A student with this email already exists.')
        return value

    def validate_registration_number(self, value):
        if Student.objects.filter(registration_number=value).exists():
            raise serializers.ValidationError('This registration number is already in use.')
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')

        user = User.objects.create_user(
            email=validated_data['email'],
            name=f"{validated_data['first_name']} {validated_data['last_name']}",
            password=password,
            role=User.Role.STUDENT,
        )
        user.is_staff = False
        user.save(update_fields=['is_staff'])

        student = Student.objects.create(
            registration_number=validated_data['registration_number'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            email=validated_data['email'],
            phone=validated_data.get('phone', ''),
            password=password,
            user=user,
        )
        return student


class ManagerRegisterSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(
            email=validated_data['email'],
            name=validated_data['name'],
            password=password,
            role=User.Role.TRANSPORT_MANAGER,
        )
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        # Use username=... to be compatible with Django's authentication backends
        # (the project's `User.USERNAME_FIELD` is `email`). Passing `username`
        # ensures `ModelBackend` maps correctly regardless of backend implementation.
        user = authenticate(username=attrs['email'], password=attrs['password'])
        if not user:
            raise serializers.ValidationError('Invalid email or password.')
        if not user.is_active:
            raise serializers.ValidationError('This account is inactive.')
        attrs['user'] = user
        return attrs


class TokenResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()


class ChangePasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({'new_password_confirm': 'Passwords do not match.'})
        try:
            student = Student.objects.get(email=attrs['email'])
            attrs['student'] = student
        except Student.DoesNotExist:
            raise serializers.ValidationError({'email': 'No student account found with this email.'})
        return attrs


class DriverSerializer(serializers.ModelSerializer):
    assigned_bus_detail = serializers.SerializerMethodField(read_only=True)
    has_portal_account = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Driver
        fields = [
            'driver_id', 'first_name', 'last_name', 'email', 'phone',
            'license_number', 'assigned_bus', 'assigned_bus_detail', 'is_active',
            'has_portal_account', 'password',
        ]
        read_only_fields = ['driver_id', 'password']

    def get_assigned_bus_detail(self, obj):
        if obj.assigned_bus:
            from apps.buses.serializers import BusSerializer
            return BusSerializer(obj.assigned_bus).data
        return None

    def get_has_portal_account(self, obj):
        return obj.user_id is not None


class DriverCreateSerializer(serializers.ModelSerializer):
    """Manager creates a driver; optional portal_password provisions JWT login."""

    portal_password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Driver
        fields = [
            'driver_id', 'first_name', 'last_name', 'email', 'phone',
            'license_number', 'assigned_bus', 'is_active', 'portal_password',
        ]
        read_only_fields = ['driver_id']

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value

    def validate_portal_password(self, value):
        if value:
            validate_password(value)
        return value

    def validate_phone(self, value):
        try:
            return normalize_phone(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))

    def validate_assigned_bus(self, value):
        validate_driver_assigned_bus(value, exclude_driver_id=None)
        return value

    def create(self, validated_data):
        portal_password = validated_data.pop('portal_password', '') or ''
        driver = Driver.objects.create(password=portal_password, **validated_data)
        if portal_password:
            user = User.objects.create_user(
                email=driver.email,
                name=f'{driver.first_name} {driver.last_name}',
                password=portal_password,
                role=User.Role.DRIVER,
            )
            user.is_staff = False
            user.save(update_fields=['is_staff'])
            driver.user = user
            driver.save(update_fields=['user'])
        parts = ['Your driver profile was created by your transport manager.']
        if driver.assigned_bus_id:
            bus = driver.assigned_bus
            reg = bus.registration_number if bus else str(driver.assigned_bus_id)
            parts.append(f'Assigned bus: {reg}.')
        notify_driver_manager_update(driver, ' '.join(parts))
        return driver

    def to_representation(self, instance):
        return DriverSerializer(instance).data


class DriverMeSerializer(serializers.ModelSerializer):
    """Driver-facing profile (includes linked user summary)."""

    assigned_bus_detail = serializers.SerializerMethodField(read_only=True)
    unread_notifications = serializers.SerializerMethodField(read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = Driver
        fields = [
            'driver_id', 'first_name', 'last_name', 'email', 'phone',
            'license_number', 'assigned_bus', 'assigned_bus_detail', 'is_active',
            'unread_notifications', 'user',
        ]
        read_only_fields = ['driver_id', 'license_number', 'email', 'user']

    def get_unread_notifications(self, obj):
        from apps.notifications.models import Notification

        return Notification.objects.filter(driver=obj, is_read=False).count()

    def get_assigned_bus_detail(self, obj):
        if obj.assigned_bus:
            from apps.buses.serializers import BusSerializer
            return BusSerializer(obj.assigned_bus).data
        return None


class DriverMeUpdateSerializer(serializers.ModelSerializer):
    """Driver may update limited profile fields."""

    class Meta:
        model = Driver
        fields = ['first_name', 'last_name', 'phone']

    def validate_phone(self, value):
        try:
            return normalize_phone(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        if instance.user_id:
            instance.user.name = f'{instance.first_name} {instance.last_name}'
            instance.user.save(update_fields=['name'])
        return instance


class PatchedDriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'license_number', 'assigned_bus', 'is_active',
        ]


class DriverManageSerializer(serializers.ModelSerializer):
    """Manager PATCH driver — optional portal_password creates or updates login."""

    portal_password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Driver
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'license_number', 'assigned_bus', 'is_active', 'portal_password',
        ]

    def validate_portal_password(self, value):
        if value:
            validate_password(value)
        return value

    def validate_email(self, value):
        instance = self.instance
        if instance is None:
            return value
        user_qs = User.objects.filter(email=value)
        if instance.user_id:
            user_qs = user_qs.exclude(pk=instance.user_id)
        if user_qs.exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value

    def validate_phone(self, value):
        try:
            return normalize_phone(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))

    def validate_assigned_bus(self, value):
        validate_driver_assigned_bus(value, exclude_driver_id=self.instance.driver_id)
        return value

    def update(self, instance, validated_data):
        snap = {
            'first_name': instance.first_name,
            'last_name': instance.last_name,
            'email': instance.email,
            'phone': instance.phone,
            'license_number': instance.license_number,
            'assigned_bus_id': instance.assigned_bus_id,
            'is_active': instance.is_active,
        }
        portal_password = validated_data.pop('portal_password', '') or ''
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        if validated_data:
            instance.save()

        if portal_password:
            instance.password = portal_password
            instance.save(update_fields=['password'])
            if instance.user_id:
                instance.user.set_password(portal_password)
                instance.user.email = instance.email
                instance.user.name = f'{instance.first_name} {instance.last_name}'
                instance.user.save(update_fields=['password', 'email', 'name'])
            else:
                if User.objects.filter(email=instance.email).exists():
                    raise serializers.ValidationError(
                        {'email': 'A user already exists with this email; use another driver email or admin.'}
                    )
                user = User.objects.create_user(
                    email=instance.email,
                    name=f'{instance.first_name} {instance.last_name}',
                    password=portal_password,
                    role=User.Role.DRIVER,
                )
                user.is_staff = False
                user.save(update_fields=['is_staff'])
                instance.user = user
                instance.save(update_fields=['user', 'password'])
        elif instance.user_id:
            instance.user.email = instance.email
            instance.user.name = f'{instance.first_name} {instance.last_name}'
            instance.user.save(update_fields=['email', 'name'])

        msgs = []
        if snap['first_name'] != instance.first_name or snap['last_name'] != instance.last_name:
            msgs.append(f'Your name was updated to {instance.first_name} {instance.last_name}.')
        if snap['email'] != instance.email:
            msgs.append(f'Your account email is now {instance.email}.')
        if snap['phone'] != instance.phone:
            msgs.append(f'Your phone on file is now {instance.phone or "(cleared)"}.')
        if snap['license_number'] != instance.license_number:
            msgs.append(f'Your license number on file is now {instance.license_number}.')
        if snap['assigned_bus_id'] != instance.assigned_bus_id:
            if instance.assigned_bus_id:
                bus = instance.assigned_bus
                reg = bus.registration_number if bus else str(instance.assigned_bus_id)
                msgs.append(f'Your assigned bus is now {reg}.')
            else:
                msgs.append('Your bus assignment was removed.')
        if snap['is_active'] != instance.is_active:
            msgs.append(
                'Your driver account is now active.'
                if instance.is_active
                else 'Your driver account was marked inactive by your manager.'
            )
        if portal_password:
            msgs.append('Your driver portal password was updated by your manager.')
        if msgs:
            notify_driver_manager_update(instance, ' '.join(msgs))

        return instance

    def to_representation(self, instance):
        return DriverSerializer(instance).data
