from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from apps.lines.serializers import DriverAssignedLineSerializer
from apps.trips.models import Trip
from apps.trips.serializers import TripSerializer

from .driver_bus_lines import lines_queryset_all_assigned_for_driver_bus, lines_queryset_for_driver_bus
from .tokens import CustomAccessToken

from .models import Driver, Student, User
from .permissions import IsAdminOrManager, IsDriver
from .serializers import (
    ChangePasswordSerializer,
    DriverCreateSerializer,
    DriverManageSerializer,
    DriverMeSerializer,
    DriverMeUpdateSerializer,
    DriverSerializer,
    LoginSerializer,
    ManagerRegisterSerializer,
    RegisterSerializer,
    StudentDetailSerializer,
    StudentSerializer,
    TokenResponseSerializer,
    UserSerializer,
)


@extend_schema(tags=['auth'])
class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary='Register a new student',
        request=RegisterSerializer,
        responses={
            201: StudentSerializer,
            400: OpenApiResponse(description='Validation errors'),
        },
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        student = serializer.save()
        return Response(StudentSerializer(student).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=['auth'])
class ManagerRegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary='Register a new transport manager account',
        request=ManagerRegisterSerializer,
        responses={
            201: TokenResponseSerializer,
            400: OpenApiResponse(description='Validation errors'),
        },
    )
    def post(self, request):
        serializer = ManagerRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        access = CustomAccessToken.for_user(user)
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(access),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
        }, status=status.HTTP_201_CREATED)


@extend_schema(tags=['auth'])
class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary='Login and obtain JWT tokens',
        request=LoginSerializer,
        responses={
            200: TokenResponseSerializer,
            400: OpenApiResponse(description='Invalid credentials'),
        },
    )
    def post(self, request):
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f'LoginView.post() received request.data: {request.data}')
        logger.info(f'LoginView.post() request.content_type: {request.content_type}')
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f'LoginSerializer validation failed: {serializer.errors}')
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        access = CustomAccessToken.for_user(user)
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(access),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
        })


@extend_schema(tags=['auth'], summary='Refresh JWT access token')
class CustomTokenRefreshView(TokenRefreshView):
    pass


@extend_schema(tags=['auth'])
class ChangePasswordView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary='Reset student password by email',
        request=ChangePasswordSerializer,
        responses={
            200: OpenApiResponse(description='Password updated successfully.'),
            400: OpenApiResponse(description='Validation errors'),
        },
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        student = serializer.validated_data['student']
        new_password = serializer.validated_data['new_password']

        # Update the password on the linked User account
        user = student.user
        if user is None:
            return Response({'detail': 'No user account linked to this student.'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save(update_fields=['password'])

        # Also store plain password on Student model (matches existing pattern)
        student.password = new_password
        student.save(update_fields=['password'])

        return Response({'detail': 'Password updated successfully.'}, status=status.HTTP_200_OK)


@extend_schema(tags=['accounts'])
class DriverMeView(APIView):
    permission_classes = [IsAuthenticated, IsDriver]

    @extend_schema(
        summary='Get own driver profile',
        responses={200: DriverMeSerializer},
    )
    def get(self, request):
        driver = request.user.driver_profile
        return Response(DriverMeSerializer(driver).data)

    @extend_schema(
        summary='Update own driver profile',
        request=DriverMeUpdateSerializer,
        responses={200: DriverMeSerializer},
    )
    def patch(self, request):
        driver = request.user.driver_profile
        serializer = DriverMeUpdateSerializer(driver, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        driver.refresh_from_db()
        return Response(DriverMeSerializer(driver).data)


@extend_schema(tags=['accounts'])
class DriverTripsListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsDriver]
    serializer_class = TripSerializer

    @extend_schema(summary='List trips for my assigned bus')
    def get_queryset(self):
        bus = self.request.user.driver_profile.assigned_bus
        if bus is None:
            return Trip.objects.none()
        return Trip.objects.filter(bus=bus).select_related(
            'schedule__line', 'bus',
        ).order_by('-trip_id')


@extend_schema(tags=['accounts'])
class DriverLinesListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsDriver]
    serializer_class = DriverAssignedLineSerializer
    pagination_class = None

    @extend_schema(summary='Assigned lines for my bus (stations + active assignment flag)')
    def get_queryset(self):
        return lines_queryset_all_assigned_for_driver_bus(self.request.user.driver_profile)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['driver_bus'] = self.request.user.driver_profile.assigned_bus
        return ctx


@extend_schema(tags=['accounts'])
class StudentMeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Get own student profile',
        responses={200: StudentDetailSerializer},
    )
    def get(self, request):
        try:
            student = request.user.student_profile
        except Student.DoesNotExist:
            return Response({'detail': 'No student profile found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(StudentDetailSerializer(student).data)

    @extend_schema(
        summary='Update own student profile',
        request=StudentSerializer,
        responses={200: StudentSerializer},
    )
    def put(self, request):
        try:
            student = request.user.student_profile
        except Student.DoesNotExist:
            return Response({'detail': 'No student profile found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = StudentSerializer(student, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


@extend_schema(tags=['accounts'])
class StudentDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Student dashboard — active subscription, recent seat, unread notifications count',
        responses={200: None},
    )
    def get(self, request):
        try:
            student = request.user.student_profile
        except Student.DoesNotExist:
            return Response({'detail': 'No student profile found.'}, status=status.HTTP_404_NOT_FOUND)

        active_sub = student.subscriptions.filter(is_active=True).first()
        from apps.notifications.constants import MANAGER_ONLY_NOTIFICATION_TYPES

        student_notif_qs = student.notifications.exclude(
            notification_type__in=MANAGER_ONLY_NOTIFICATION_TYPES
        )
        unread_count = student_notif_qs.filter(is_read=False).count()
        seat = student.seat_assignments.select_related('trip', 'row').filter(
            trip__status='in_progress'
        ).first()

        recent_notifications = student_notif_qs.order_by('-created_at')[:5]
        from apps.notifications.serializers import NotificationSerializer
        notifications_data = NotificationSerializer(recent_notifications, many=True).data

        return Response({
            'student': StudentSerializer(student).data,
            'active_subscription': {
                'line_id': active_sub.line_id if active_sub else None,
                'line_name': active_sub.line.name if active_sub else None,
            } if active_sub else None,
            'current_seat': {
                'row_number': seat.row.row_number if seat else None,
                'seat_number': seat.seat_number if seat else None,
                'trip_id': seat.trip_id if seat else None,
            } if seat else None,
            'unread_notifications': unread_count,
            'recent_activity': notifications_data,
        })


@extend_schema(tags=['accounts'])
class ManagerDashboardView(APIView):
    permission_classes = [IsAdminOrManager]

    @extend_schema(
        summary='Manager dashboard — system overview stats and alerts',
        responses={200: None},
    )
    def get(self, request):
        from apps.buses.models import Bus, BusAssignment
        from apps.incidents.models import Incident
        from apps.lines.models import Line
        from apps.trips.models import Trip

        total_students = Student.objects.count()
        total_lines = Line.objects.count()
        active_trips = Trip.objects.filter(status='in_progress').count()
        available_buses = Bus.objects.filter(status='available').count()
        open_incidents = Incident.objects.filter(resolved=False).count()
        total_drivers = Driver.objects.count()

        unresolved_incidents = (
            Incident.objects.filter(resolved=False, show_on_manager_dashboard_alerts=True)
            .select_related('trip__schedule__line', 'line')
            .order_by('-reported_at')[:5]
        )
        from apps.incidents.serializers import IncidentSerializer
        incidents_data = IncidentSerializer(unresolved_incidents, many=True).data

        return Response({
            'stats': {
                'total_students': total_students,
                'total_lines': total_lines,
                'active_trips': active_trips,
                'available_buses': available_buses,
                'open_incidents': open_incidents,
                'total_drivers': total_drivers,
            },
            'system_alerts': incidents_data,
        })


@extend_schema(tags=['accounts'])
@extend_schema_view(
    get=extend_schema(summary='List all students (Manager only)'),
)
class StudentListView(generics.ListAPIView):
    queryset = Student.objects.all().order_by('last_name', 'first_name')
    serializer_class = StudentDetailSerializer
    permission_classes = [IsAdminOrManager]


@extend_schema(tags=['accounts'])
@extend_schema_view(
    get=extend_schema(summary='Retrieve student detail (Manager only)'),
    put=extend_schema(summary='Update student (Manager only)'),
    patch=extend_schema(summary='Partial update student (Manager only)'),
    delete=extend_schema(summary='Delete student (Manager only)'),
)
class StudentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentDetailSerializer
    permission_classes = [IsAdminOrManager]
    lookup_field = 'student_id'


@extend_schema(tags=['accounts'])
@extend_schema_view(
    get=extend_schema(summary='List all drivers (Manager only)'),
    post=extend_schema(summary='Create a driver (Manager only)'),
)
class DriverListView(generics.ListCreateAPIView):
    queryset = Driver.objects.select_related('assigned_bus').all().order_by('last_name', 'first_name')
    permission_classes = [IsAdminOrManager]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DriverCreateSerializer
        return DriverSerializer


@extend_schema(tags=['accounts'])
@extend_schema_view(
    get=extend_schema(summary='Retrieve driver detail (Manager only)'),
    put=extend_schema(summary='Update driver (Manager only)'),
    patch=extend_schema(summary='Partial update driver (Manager only)'),
    delete=extend_schema(summary='Delete driver (Manager only)'),
)
class DriverDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Driver.objects.select_related('assigned_bus').all()
    permission_classes = [IsAdminOrManager]
    lookup_field = 'driver_id'

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return DriverManageSerializer
        return DriverSerializer
