from django.contrib import admin
from django.urls import include, path
from django.views.generic.base import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from .health import health

from apps.accounts.urls import auth_urlpatterns, student_urlpatterns

urlpatterns = [
    # Root redirect to API root
    path('', RedirectView.as_view(url='/api/', permanent=False)),

    # Django admin
    path('admin/', admin.site.urls),

    # OpenAPI / Swagger
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Authentication
    path('api/', include((auth_urlpatterns, 'auth'))),

    # Health check for smoke tests
    path('api/health/', health),

    # Student profile & dashboard
    path('api/', include((student_urlpatterns, 'accounts'))),

    # Lines & Stations
    path('api/', include('apps.lines.urls')),

    # Schedules
    path('api/', include('apps.schedules.urls')),

    # Buses & Bus Assignments
    path('api/', include('apps.buses.urls')),

    # Subscriptions
    path('api/', include('apps.subscriptions.urls')),

    # Trips, Rows, Seat Assignments
    path('api/', include('apps.trips.urls')),

    # Incidents
    path('api/', include('apps.incidents.urls')),

    # Notifications
    path('api/', include('apps.notifications.urls')),

    # Reports
    path('api/', include('apps.reports.urls')),
]
