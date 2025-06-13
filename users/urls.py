
from django.urls import path
from .views import HomePropertyListView, HomePropertyListView, PropertyDetailView, book_property, move_in_notice, chat_view, recent_chats_api_view 

app_name = 'users'

urlpatterns = [

    path('', HomePropertyListView.as_view(), name='home'),
    path('property/<int:pk>/', PropertyDetailView.as_view(), name='property_detail'),
    path('property/<int:pk>/book/', book_property, name='book_property'), # NEW Booking URL
    path('booking/<int:booking_pk>/notice/', move_in_notice, name='move_in_notice'), # NEW Move-in Notice URL
    path('property/<int:property_pk>/chat/<int:other_user_pk>/', chat_view, name='chat_with_user'), # NEW Chat URL
    path('api/recent-chats/', recent_chats_api_view, name='recent_chats_api'), # NEW API URL

]