from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('record-attendance/', views.record_attendance, name='record_attendance'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('reset-attendance/', views.reset_attendance, name='reset_attendance'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='attendance/login.html'), name='logout'),
]

