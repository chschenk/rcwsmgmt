#!/bin/sh
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py compilemessages

# Start Gunicorn processes
exec gunicorn rcwsmgmt.wsgi:application \
        --bind 0.0.0.0:8000 \
        --workers 3 \
	--access-logfile /var/log/gunicorn-access.log \
	--error-logfile /var/log/gunicorn-error.log
