from django.urls import path
from . import views

  
urlpatterns = [
    path('',views.index, name="index"),
    
]

'''
    path('AdvisorAchievement', views.advisorAchievement, name ="AdvisorAchievement")
'''