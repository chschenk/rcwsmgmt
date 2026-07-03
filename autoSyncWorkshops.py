#!/usr/bin/env python
"""Auto sync workshops from pretix to database."""
import os
import datetime
import time
import logging

from django.core.management import execute_from_command_line


def auto_sync_enabled():
	from base.models import get_runtime_setting

	return get_runtime_setting('AUTO_SYNC_ENABLED', '1') != '0'

def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rcwsmgmt.settings")
    while True:
        now = datetime.datetime.now()
        if now.minute == 0 and now.second == 0 and auto_sync_enabled():
            try:
                execute_from_command_line(['manage.py', 'sync_workshops'])
            except Exception as e:
                logging.error(f"An error occurred while syncing workshops: {e}")
        time.sleep(1)

if __name__ == "__main__":
    main()