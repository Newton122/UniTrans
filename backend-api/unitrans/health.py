from django.http import JsonResponse
from django.db import connection
from django.contrib.auth import get_user_model


def health(request):
    """Simple health endpoint used by smoke tests to verify DB and auth availability.

    Returns JSON with `ok`, `db` and `users` (count) fields when healthy.
    """
    try:
        # Basic DB connectivity check
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
        User = get_user_model()
        user_count = User.objects.count()
        return JsonResponse({'ok': True, 'db': True, 'users': user_count})
    except Exception as exc:
        return JsonResponse({'ok': False, 'db': False, 'error': str(exc)}, status=503)
