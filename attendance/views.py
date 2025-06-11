from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.urls import reverse
from django.db import models
from .models import Employee, Attendance, Department
from calendar import monthrange
from datetime import datetime, time
import calendar

def is_superuser(user):
    return user.is_superuser

class CustomLoginView(LoginView):
    template_name = 'attendance/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        user = self.request.user
        if user.is_authenticated and user.is_superuser:
            return reverse('admin_dashboard')
        return reverse('dashboard')

@login_required
def dashboard(request):
    try:
        employee = request.user.employee
    except Employee.DoesNotExist:
        messages.error(request, "You are not registered as an employee.")
        return redirect('login')

    today = timezone.now().date()
    incomplete_attendances = Attendance.objects.filter(
        employee=employee,
        check_out__isnull=True,
        date__lt=today
    )
    for attendance in incomplete_attendances:
        attendance.check_out = timezone.make_aware(
            datetime.combine(attendance.date, time(18, 0)),
            timezone.get_current_timezone()
        )
        attendance.save()

    attendance = Attendance.objects.filter(employee=employee, date=today).first()
    history = Attendance.objects.filter(employee=employee).order_by('-date')[:30]

    return render(request, 'attendance/dashboard.html', {
        'employee': employee,
        'today_attendance': attendance,
        'history': history
    })

@login_required
def record_attendance(request):
    try:
        employee = request.user.employee
    except Employee.DoesNotExist:
        messages.error(request, "You are not registered as an employee.")
        return redirect('login')

    today = timezone.now().date()
    attendance = Attendance.objects.filter(employee=employee, date=today).first()
    is_checked_in = attendance and not attendance.check_out

    if request.method == 'POST':
        comments = request.POST.get('comments', '')
        if not attendance:
            Attendance.objects.create(
                employee=employee,
                check_in=timezone.now(),
                date=today,
                comments=comments,
                status='Present'
            )
            messages.success(request, "Check-in recorded successfully.")
        elif is_checked_in:
            attendance.check_out = timezone.now()
            attendance.comments = comments
            attendance.save()
            messages.success(request, "Check-out recorded successfully.")
        else:
            messages.warning(request, "Attendance already completed for today.")
        return redirect('dashboard')

    return render(request, 'attendance/record_attendance.html', {
        'employee': employee,
        'is_checked_in': is_checked_in
    })

@login_required
def employee_profile(request):
    try:
        employee = request.user.employee
    except Employee.DoesNotExist:
        messages.error(request, "You are not registered as an employee.")
        return redirect('login')
    
    attendance_records = Attendance.objects.filter(employee=employee).order_by('-date')[:30]
    return render(request, 'attendance/employee_profile.html', {
        'employee': employee,
        'attendance_records': attendance_records
    })

@login_required
@user_passes_test(is_superuser)
def admin_employee_list(request):
    employees = Employee.objects.all()
    return render(request, 'attendance/admin_employee_list.html', {
        'employees': employees
    })

@login_required
@user_passes_test(is_superuser)
def admin_employee_detail(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    attendance_records = Attendance.objects.filter(employee=employee).order_by('-date')[:30]
    return render(request, 'attendance/admin_employee_detail.html', {
        'employee': employee,
        'attendance_records': attendance_records
    })

@login_required
@user_passes_test(is_superuser)
def admin_bank_info(request):
    employees = Employee.objects.filter(bank_account_number__isnull=False)
    return render(request, 'attendance/admin_bank_info.html', {
        'employees': employees
    })

@login_required
@user_passes_test(is_superuser)
def admin_dashboard(request):
    employees = Employee.objects.all()
    today = timezone.now().date()
    current_year = today.year
    current_month = today.month

    incomplete_attendances = Attendance.objects.filter(
        check_out__isnull=True,
        date__lt=today
    )
    for attendance in incomplete_attendances:
        attendance.check_out = timezone.make_aware(
            datetime.combine(attendance.date, time(18, 0)),
            timezone.get_current_timezone()
        )
        attendance.save()

    _, days_in_month = monthrange(current_year, current_month)
    working_days = 0
    for day in range(1, days_in_month + 1):
        date = datetime(current_year, current_month, day)
        if date.weekday() not in [5, 6]:
            working_days += 1

    attendance_summary = []
    for employee in employees:
        present_days = Attendance.objects.filter(
            employee=employee,
            date__year=current_year,
            date__month=current_month,
            status='Present'
        ).values('date').distinct().count()
        total_hours = Attendance.objects.filter(
            employee=employee,
            date__year=current_year,
            date__month=current_month,
            hours_worked__isnull=False
        ).aggregate(total_hours=models.Sum('hours_worked'))['total_hours'] or 0
        absent_days = working_days - present_days
        attendance_summary.append({
            'employee': employee,
            'present_days': present_days,
            'total_hours': total_hours,
            'absent_days': absent_days
        })
    half_day_records = Attendance.objects.filter(
        date__year=current_year,
        date__month=current_month,
        hours_worked__lte=4,
        hours_worked__isnull=False,
        status='Present'
    ).select_related('employee').order_by('date', 'employee')

    attendance_records = Attendance.objects.filter(date=today).order_by('-date')

    return render(request, 'attendance/admin_dashboard.html', {
        'employees': employees,
        'attendance_records': attendance_records,
        'working_days': working_days,
        'attendance_summary': attendance_summary,
        'current_month': calendar.month_name[current_month],
        'current_year': current_year,
        'half_day_records': half_day_records
    })

@login_required
@user_passes_test(is_superuser)
def reset_attendance(request):
    if request.method == 'POST':
        Attendance.objects.all().delete()
        messages.success(request, "Attendance records have been reset successfully.")
        return redirect('admin_dashboard')
    return render(request, 'attendance/reset_attendance.html')

@login_required
def birthday_calendar(request):
    employees = Employee.objects.filter(dob__isnull=False).select_related('department')
    birthday_data = []
    months = ['January', 'February', 'March', 'April', 'May', 'June', 
              'July', 'August', 'September', 'October', 'November', 'December']
    
    for month in range(12):
        month_data = {
            'month': months[month],
            'days': [{'count': 0, 'employees': []} for _ in range(31)]
        }
        for employee in employees:
            if employee.dob.month == month + 1:
                day = employee.dob.day - 1
                month_data['days'][day]['count'] += 1
                month_data['days'][day]['employees'].append({
                    'first_name': employee.first_name,
                    'last_name': employee.last_name,
                    'department': employee.department.name if employee.department else 'Not assigned',
                    'position': employee.position or 'Not provided'
                })
        birthday_data.append(month_data)
    
    return render(request, 'attendance/birthday_calendar.html', {
        'birthday_data': birthday_data
    })