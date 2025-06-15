from django.contrib import admin
from django.urls import path, include
from django.urls.conf import include  
from django.conf import settings  
from django.conf.urls.static import static

from signup.views import landlord_signup_view 
from signup.views import student_signup_view 


app_name = "signup"
urlpatterns = [
   

    path('landlord_signup_view', landlord_signup_view, name='landlord_signup_view'),
    path('student_signup_view', student_signup_view, name='student_signup_view'),




]