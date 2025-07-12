from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import viewsets, status
from .models import Listing, Booking, Payment, CustomUser
from .serializers import ListingSerializer, BookingSerializer, PaymentSerializer, CustomUserSerializer
import uuid
import requests
from django.conf import settings
from django.shortcuts import get_object_or_404
from .tasks import send_booking_email

@api_view(['GET'])
def index(request):
    return Response({"message": "Welcome to the ALX Travel App!"})

class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer  

class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer

    def perform_create(self, serializer):
        booking = serializer.save()

        # Prepare email data
        user_email = booking.user.email
        booking_details = (
            f"Booking ID: {booking.id}\n"
            f"Check-in: {booking.check_in}\n"
            f"Check-out: {booking.check_out}\n"
            f"Listing: {booking.listing.title}\n"
            f"Total Price: {float(booking.listing.price_per_night) * (booking.check_out - booking.check_in).days} ETB"
        )

        # Send email via Celery
        send_booking_email.delay(user_email, booking_details)


class MyPaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

@api_view(['POST'])
def initiate_payment(request):
    booking_id = request.data.get('booking_id')
    phone_number = request.data.get('phone_number')

    booking = get_object_or_404(Booking, id=booking_id)
    tx_ref = f"booking-{uuid.uuid4()}"
    amount = float(booking.listing.price_per_night)  * (booking.check_out - booking.check_in).days

    payload = {
        "amount": str(amount),
        "currency": "ETB",
        "email": request.user.email,
        "first_name": request.user.first_name,
        "last_name": request.user.last_name,
        "phone_number": phone_number,
        "tx_ref": tx_ref,
        "callback_url": "https://webhook.site/077164d6-29cb-40df-ba29-8a00e59a7e60",
        "return_url": "https://www.google.com/",
        "customization": {
            "title": "Booking Payment",
            "description": f"Payment for Booking #{booking.id}"
        }
    }

    headers = {
        "Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    chapa_response = requests.post("https://api.chapa.co/v1/transaction/initialize", json=payload, headers=headers)
    data = chapa_response.json()

    if data.get("status") == "success":
        payment = Payment.objects.create(
            booking=booking,
            amount=amount,
            chapa_tx_ref=tx_ref,
            chapa_checkout_url=data['data']['checkout_url'],
            status="Pending",
            response_log=data
        )
        return Response({
            "checkout_url": data['data']['checkout_url'],
            "tx_ref": tx_ref
        }, status=status.HTTP_200_OK)
    else:
        return Response({"error": data.get("message", "Payment initiation failed")}, status=status.HTTP_400_BAD_REQUEST)
    

@api_view(['GET'])
def verify_payment(request, tx_ref):
    url = f"https://api.chapa.co/v1/transaction/verify/{tx_ref}"
    headers = {
        "Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}"
    }

    chapa_response = requests.get(url, headers=headers)
    data = chapa_response.json()

    if data.get("status") == "success":
        try:
            payment = Payment.objects.get(chapa_tx_ref=tx_ref)
            payment.status = "Completed" if data['data']['status'] == "success" else "Failed"
            payment.chapa_tx_id = data['data']['reference']
            payment.response_log = data
            payment.save()
            return Response({
                "message": "Payment verified",
                "status": payment.status
            }, status=status.HTTP_200_OK)
        except Payment.DoesNotExist:
            return Response({"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)
    else:
        return Response({
            "error": "Verification failed",
            "detail": data.get("message", "Unknown error"),
            "data": data
        }, status=status.HTTP_400_BAD_REQUEST)