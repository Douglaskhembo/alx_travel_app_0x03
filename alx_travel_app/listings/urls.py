from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ListingViewSet, BookingViewSet,CustomUserViewSet, MyPaymentViewSet as PaymentViewSet, initiate_payment, verify_payment
from . import views

router = DefaultRouter()
router.register(r'listings', ListingViewSet, basename='listing')
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'payments', PaymentViewSet, basename='payment') 
router.register(r'users', CustomUserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    path('welcome/', views.index, name='index'),
    path('chapa/initiate/', initiate_payment, name='initiate-payment'),
    path('chapa/verify/<str:tx_ref>/', verify_payment, name='verify-payment'),
]
