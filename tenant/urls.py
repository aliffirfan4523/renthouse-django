from django.urls import path
from . import views

app_name = 'tenant'
  
urlpatterns = [
    path('',views.tenant_home, name="tenant_home"),
    
]

'''
    path('AdvisorAchievement', views.advisorAchievement, name ="AdvisorAchievement")
'''