from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.urls import reverse
from django.db import models
from .models import Employee, Attendance, Department
from calendar import monthrange
from datetime import datetime, time, timedelta
import calendar
import nepali_datetime
from nepali_datetime import date as nepali_date
import re

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
    employees = Employee.objects.filter(dob_nepali__isnull=False).select_related('department')
    
    # Nepali months in order
    nepali_months = [
        'Baisakh', 'Jestha', 'Asadh', 'Shrawan', 'Bhadra', 'Ashoj',
        'Kartik', 'Mangsir', 'Poush', 'Magh', 'Falgun', 'Chaitra'
    ]
    
    # Initialize Nepali birthday data: 12 months, each with 31 days
    nepali_birthday_data = []
    for month_idx, month_name in enumerate(nepali_months):
        month_data = {
            'month': month_name,
            'days': [{'count': 0, 'employees': []} for _ in range(31)]
        }
        nepali_birthday_data.append(month_data)
    
    # Parse nepali_dob (YYYY-MM-DD or YYYY/MM/DD) and map to calendar
    dob_pattern = re.compile(r'^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$')
    for employee in employees:
        if employee.dob_nepali:
            match = dob_pattern.match(employee.dob_nepali)
            if match:
                year, month, day = map(int, match.groups())
                # Validate month (1-12) and day (1-31)
                if 1 <= month <= 12 and 1 <= day <= 31:
                    month_idx = month - 1  # 0-based index for Baisakh=0
                    day_idx = day - 1      # 0-based index for day
                    nepali_birthday_data[month_idx]['days'][day_idx]['count'] += 1
                    nepali_birthday_data[month_idx]['days'][day_idx]['employees'].append({
                        'first_name': employee.first_name,
                        'last_name': employee.last_name,
                        'department': employee.department.name if employee.department else 'Not assigned',
                        'position': employee.position or 'Not provided'
                    })
    
    # Get today's Nepali date
    today_nepali = nepali_datetime.date.today()
    today_nepali_date = {
        'year': today_nepali.year,
        'month': today_nepali.month,
        'day': today_nepali.day
    }
    mahina=nepali_months[(today_nepali.month)-1]
    return render(request, 'attendance/birthday_calendar.html', {
        'nepali_birthday_data': nepali_birthday_data,
        'nepali_months': nepali_months,
        'today_nepali_date': today_nepali_date,
        'mahina':mahina
    })

# CHANGED: attendance_calendar view (admin-only, Gregorian dates, historical months)
@login_required
@user_passes_test(is_superuser)
def attendance_calendar(request):
    employees = Employee.objects.all().order_by('first_name', 'last_name')
    
    today = timezone.now().date()
    current_year = today.year
    current_month = today.month
    current_day = today.day
    
    # Get selected month and year from GET parameters, default to current
    selected_year = int(request.GET.get('year', current_year))
    selected_month = int(request.GET.get('month', current_month))
    
    try:
        datetime(selected_year, selected_month, 1)
    except ValueError:
        selected_year = current_year
        selected_month = current_month
    
    _, days_in_month = monthrange(selected_year, selected_month)
    month_name = calendar.month_name[selected_month]
    
    # Get available months with records, sorted descending
    earliest_record = Attendance.objects.order_by('date').first()
    available_months = []
    if earliest_record:
        start_date = earliest_record.date
        current_date = datetime(current_year, current_month, 1)
        year = start_date.year
        month = start_date.month
        while datetime(year, month, 1) <= current_date:
            available_months.append({
                'year': year,
                'month': month,
                'month_name': calendar.month_name[month]
            })
            month += 1
            if month > 12:
                month = 1
                year += 1
        available_months.sort(key=lambda x: (x['year'], x['month']), reverse=True)
    
    attendance_data = []
    for employee in employees:
        employee_data = {
            'employee': {'id': employee.id, 'name': f"{employee.first_name} {employee.last_name}"},
            'days': [{'status': None, 'details': []} for _ in range(days_in_month)]
        }
        attendance_data.append(employee_data)
    
    attendance_records = Attendance.objects.filter(
        date__year=selected_year,
        date__month=selected_month
    ).select_related('employee')
    
    for record in attendance_records:
        employee_idx = next((i for i, data in enumerate(attendance_data) if data['employee']['id'] == record.employee.id), None)
        if employee_idx is not None:
            day_idx = record.date.day - 1
            if 0 <= day_idx < days_in_month:
                check_in = record.check_in.strftime('%H:%M') if record.check_in else 'N/A'
                check_out = record.check_out.strftime('%H:%M') if record.check_out else 'N/A'
                hours = record.hours_worked or 0
                attendance_data[employee_idx]['days'][day_idx] = {
                    'status': record.status,
                    'details': [{
                        'check_in': check_in,
                        'check_out': check_out,
                        'hours_worked': hours
                    }]
                }
    
    return render(request, 'attendance/attendance_calendar.html', {
        'attendance_data': attendance_data,
        'current_month_name': month_name,
        'current_year': selected_year,
        'selected_month': selected_month,  # Pass selected month
        'selected_year': selected_year,   # Pass selected year
        'today_date': {'year': current_year, 'month': current_month, 'day': current_day},
        'days_in_month': range(1, days_in_month + 1),
        'available_months': available_months
    })

# CHANGED: employee_attendance view to display hours and minutes
@login_required
def employee_attendance(request):
    try:
        employee = request.user.employee
    except Employee.DoesNotExist:
        messages.error(request, "You are not registered as an employee.")
        return redirect('login')

    # Fetch all attendance records for the employee
    records = Attendance.objects.filter(employee=employee).order_by('-date')

    # Group records by year and month
    monthly_records = {}
    for record in records:
        year = record.date.year
        month = record.date.month
        month_key = (year, month)
        if month_key not in monthly_records:
            monthly_records[month_key] = {
                'year': year,
                'month': month,
                'month_name': calendar.month_name[month],
                'records': []
            }
        # Convert hours_worked to hours and minutes
        hours_worked = record.hours_worked or 0
        hours = int(hours_worked)
        minutes = int((hours_worked % 1) * 60)
        monthly_records[month_key]['records'].append({
            'date': record.date,
            'status': record.status,
            'check_in': record.check_in,
            'check_out': record.check_out,
            'hours': hours,
            'minutes': minutes
        })

    # Apply weekend logic
    for month_key in monthly_records:
        records = monthly_records[month_key]['records']
        for i, record in enumerate(records):
            date = record['date']
            weekday = date.weekday()
            if weekday in [5, 6]:  # Saturday or Sunday
                friday_date = date - timedelta(days=1 if weekday == 5 else 2)
                monday_date = date + timedelta(days=2 if weekday == 5 else 1)
                friday_record = Attendance.objects.filter(employee=employee, date=friday_date).first()
                monday_record = Attendance.objects.filter(employee=employee, date=monday_date).first()
                friday_present = friday_record and friday_record.status == 'Present'
                monday_present = monday_record and monday_record.status == 'Present'
                if record['status'] != 'Present' and (friday_present or monday_present):
                    record['status'] = 'Present (Weekend Rule)'
                    record['hours'] = 8  # Assume 8 hours
                    record['minutes'] = 0
                elif record['status'] != 'Present' and not (friday_present or monday_present):
                    record['status'] = 'Absent (Weekend Rule)'
                    record['hours'] = 0
                    record['minutes'] = 0

    # Sort months in descending order (most recent first)
    sorted_months = sorted(monthly_records.values(), key=lambda x: (x['year'], x['month']), reverse=True)

    return render(request, 'attendance/employee_attendance.html', {
        'employee': employee,
        'monthly_records': sorted_months
    })