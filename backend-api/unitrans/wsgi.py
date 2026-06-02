import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unitrans.settings')

application = get_wsgi_application()

# Optional: create a superuser automatically when certain env vars are provided.
# Set `DJANGO_AUTO_SUPERUSER=1` and provide `DJANGO_SUPERUSER_USERNAME`,
# `DJANGO_SUPERUSER_EMAIL`, and `DJANGO_SUPERUSER_PASSWORD` in Render environment variables.
try:
	if os.environ.get('DJANGO_AUTO_SUPERUSER', '').lower() in ('1', 'true', 'yes'):
		from django.contrib.auth import get_user_model
		User = get_user_model()
		# Use the user model's USERNAME_FIELD for lookups and creation so this
		# works for custom user models where the username field is 'email'.
		username_field = getattr(User, 'USERNAME_FIELD', 'username')
		username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
		email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
		password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
		# Optional explicit name for the superuser; fallback to username/email
		name = os.environ.get('DJANGO_SUPERUSER_NAME') or username or email or 'admin'
		if username and password:
			lookup = {username_field: username}
			if not User.objects.filter(**lookup).exists():
				# create_superuser should accept keyword args matching the model
				create_kwargs = {username_field: username, 'email': email or '', 'name': name, 'password': password}
				User.objects.create_superuser(**create_kwargs)
				print('Auto-created superuser:', username)
			else:
				print('Superuser already exists:', username)
except Exception as exc:
	# Avoid crashing the WSGI process if something goes wrong here
	print('Auto-superuser setup skipped or failed:', exc)
