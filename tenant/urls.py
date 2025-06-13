from django.urls import path

from .views import move_in_notice
from . import views

app_name = 'tenant'
  
urlpatterns = [
    path('',views.tenant_dashboard, name="tenant_home"),
    path('cancel-bookings/<int:booking_id>',views.cancel_booking, name="cancel_booking"),
    path('notice/<int:booking_pk>/', move_in_notice, name='move_in_notice'), # NEW Move-in Notice URL
]

'''
    path('AdvisorAchievement', views.advisorAchievement, name ="AdvisorAchievement")
'''