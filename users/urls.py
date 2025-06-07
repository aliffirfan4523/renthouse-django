
from django.urls import path
from .views import HomePropertyListView, PropertyDetailView, book_property, move_in_notice, chat_view

app_name = 'users'

urlpatterns = [

    path('', HomePropertyListView.as_view(), name='home'),
    path('property/<int:pk>/', PropertyDetailView.as_view(), name='property_detail'),
    path('property/<int:pk>/book/', book_property, name='book_property'), # NEW Booking URL
    path('booking/<int:booking_pk>/notice/', move_in_notice, name='move_in_notice'), # NEW Move-in Notice URL
    path('property/<int:property_pk>/chat/<int:owner_pk>/', chat_view, name='chat_with_owner'), # NEW Chat URL

]