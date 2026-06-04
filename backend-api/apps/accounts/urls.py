from django.urls import path

from .views import (
    ChangePasswordView,
    CustomTokenRefreshView,
    DriverDetailView,
    DriverListView,
    DriverMeView,
    DriverLinesListView,
    DriverTripsListView,
    LoginView,
    ManagerDashboardView,
    ManagerRegisterView,
    RegisterView,
    StudentDashboardView,
    StudentDetailView,
    StudentListView,
    StudentMeView,
)

auth_urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/manager/register/', ManagerRegisterView.as_view(), name='auth-manager-register'),
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/token/refresh/', CustomTokenRefreshView.as_view(), name='token-refresh'),
    path('auth/reset-password/', ChangePasswordView.as_view(), name='auth-reset-password'),
]

student_urlpatterns = [
    path('students/me/', StudentMeView.as_view(), name='student-me'),
    path('students/me/dashboard/', StudentDashboardView.as_view(), name='student-dashboard'),
    path('drivers/me/', DriverMeView.as_view(), name='driver-me'),
    path('drivers/me/trips/', DriverTripsListView.as_view(), name='driver-trips'),
    path('drivers/me/lines/', DriverLinesListView.as_view(), name='driver-lines'),
    path('manager/dashboard/', ManagerDashboardView.as_view(), name='manager-dashboard'),
    path('manager/students/', StudentListView.as_view(), name='manager-student-list'),
    path('manager/students/<int:student_id>/', StudentDetailView.as_view(), name='manager-student-detail'),
    path('manager/drivers/', DriverListView.as_view(), name='manager-driver-list'),
    path('manager/drivers/<int:driver_id>/', DriverDetailView.as_view(), name='manager-driver-detail'),
]
