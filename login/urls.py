from django.urls import path
from . import views
from django.conf.urls.static import static 
from django.conf import settings  

app_name = 'login'  # <-- this is the namespace

urlpatterns = [
    path('', views.login_view, name='login'),  # This line handles /Login/
    path('logout', views.logout_view, name='logout'),
    path('register', views.register_user, name='register_user'),
    path('adminLogin', views.admin_login, name='adminLogin'),
    path('adminLogout', views.admin_logout, name='adminLogout'),
]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

