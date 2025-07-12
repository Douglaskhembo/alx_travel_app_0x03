from django.core.management.base import BaseCommand
from listings.models import Listing
from django.contrib.auth.models import User
import random

class Command(BaseCommand):
    help = 'Seed the database with sample listings'

    def handle(self, *args, **kwargs):
        host, created = User.objects.get_or_create(username='hostuser', defaults={
            'email': 'host@example.com',
            'password': 'admin123'
        })

        titles = ["Ocean View Condo", "Urban Loft", "Countryside Retreat", "Luxury Studio"]
        locations = ["Nairobi", "Mombasa", "Kisumu", "Naivasha"]

        for i in range(10):
            Listing.objects.create(
                title=f"{random.choice(titles)} #{i+1}",
                description="Sample property description.",
                location=random.choice(locations),
                price_per_night=round(random.uniform(50, 300), 2),
                available=random.choice([True, False]),
                host=host
            )

        self.stdout.write(self.style.SUCCESS("✅ Seeded 10 sample listings."))
