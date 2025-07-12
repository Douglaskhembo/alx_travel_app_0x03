from django.core.management.base import BaseCommand
from django.conf import settings
from listings.models import CustomUser


class Command(BaseCommand):
    help = "Create a default admin user with role 'ADMIN' if it doesn't exist"

    def handle(self, *args, **kwargs):
        admin_email = settings.DEFAULT_ADMIN_EMAIL
        password = settings.DEFAULT_ADMIN_PASSWORD
        first_name = getattr(settings, "DEFAULT_ADMIN_FIRST_NAME")
        last_name = getattr(settings, "DEFAULT_ADMIN_LAST_NAME",)
        phone_number = getattr(settings, "DEFAULT_ADMIN_PHONE_NUMBER")

        if not CustomUser.objects.filter(email=admin_email).exists():
            CustomUser.objects.create_user(
                email=admin_email,
                first_name=first_name,
                last_name=last_name,
                password=password,
                role="ADMIN"
            )
            self.stdout.write(self.style.SUCCESS(
                f"✅ Admin user created with email: {admin_email} and role: ADMIN"
            ))
        else:
            self.stdout.write(self.style.WARNING("⚠️ Admin user already exists."))
