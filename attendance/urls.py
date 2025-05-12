from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.employee_list, name='employee_list'),
    path('employee/<int:employee_id>/history/', views.attendance_history, name='attendance_history'),
    path('employee/<int:employee_id>/check-in-out/', views.check_in_out, name='check_in_out'),
    path('login/', auth_views.LoginView.as_view(template_name='attendance/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='attendance/login.html'), name='logout'),
] 