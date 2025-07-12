from django.apps import AppConfig
import logging

class ListingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'listings'

    def ready(self):
        # Run the admin creation command only when starting the server
        import sys
        if 'runserver' in sys.argv:
            try:
                from django.core.management import call_command
                call_command('create_admin')
            except Exception as e:
                logging.warning(f"Could not create default admin: {e}")
