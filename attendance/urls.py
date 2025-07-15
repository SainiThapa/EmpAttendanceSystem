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
    path('profile/', views.employee_profile, name='employee_profile'),
    path('employees/', views.admin_employee_list, name='admin_employee_list'),
    path('employees/<int:employee_id>/', views.admin_employee_detail, name='admin_employee_detail'),
    path('bank-info/', views.admin_bank_info, name='admin_bank_info'),
    path('birthday-calendar/', views.birthday_calendar, name='birthday_calendar'),
    path('attendance-calendar/', views.attendance_calendar, name='attendance_calendar'),
    path('employee-attendance/', views.employee_attendance, name='employee_attendance'),
]