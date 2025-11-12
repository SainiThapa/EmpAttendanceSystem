from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.urls import reverse
from django.db import models
from .models import Employee, Attendance, Department, LeaveRequest, Notice
from calendar import monthrange
from datetime import datetime, time, timedelta
import calendar
from django.db.models import Q
from .models import TaskAttachment

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
            datetime.combine(attendance.date, time(17, 0)),
            timezone.get_current_timezone()
        )
        attendance.save()

    attendance = Attendance.objects.filter(employee=employee, date=today).first()
    history = Attendance.objects.filter(employee=employee).order_by('-date')[:30]

    # Leave statistics
    leave_stats = {
        'pending': LeaveRequest.objects.filter(employee=employee, status='Pending').count(),
        'approved': LeaveRequest.objects.filter(employee=employee, status='Approved').count(),
        'rejected': LeaveRequest.objects.filter(employee=employee, status='Rejected').count(),
        'used': LeaveRequest.objects.filter(employee=employee, status='Approved').count(),
    }
    
    recent_leaves = LeaveRequest.objects.filter(employee=employee).order_by('-created_at')[:5]
    active_notices = Notice.objects.filter(is_active=True).order_by('-published_at')

    # Get today's tasks
    todo_attachments = []
    completed_attachments = []
    if attendance:
        todo_attachments = attendance.get_todo_attachments()
        completed_attachments = attendance.get_completed_attachments()

    return render(request, 'attendance/employee/dashboard.html', {
        'employee': employee,
        'today_attendance': attendance,
        'history': history,
        'leave_stats': leave_stats,
        'recent_leaves': recent_leaves,
        'active_notices': active_notices,
        'todo_attachments': todo_attachments,
        'completed_attachments': completed_attachments,
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
        action = request.POST.get('action')  # 'checkin' or 'checkout'
        
        if action == 'checkin' and not attendance:
            # Handle Check-in
            todo_tasks = request.POST.get('todo_tasks', '')
            
            # Create attendance record
            attendance = Attendance.objects.create(
                employee=employee,
                check_in=timezone.now(),
                date=today,
                todo_tasks=todo_tasks,
                status='Present'
            )
            
            # Handle multiple file uploads for to-do tasks
            todo_files = request.FILES.getlist('todo_attachments')
            for file in todo_files:
                TaskAttachment.objects.create(
                    attendance=attendance,
                    task_type='todo',
                    image=file
                )
            
            messages.success(request, "Check-in recorded successfully with to-do tasks.")
            return redirect('dashboard')
            
        elif action == 'checkout' and is_checked_in:
            # Handle Check-out
            completed_tasks = request.POST.get('completed_tasks', '')
            
            # Update attendance record
            attendance.check_out = timezone.now()
            attendance.completed_tasks = completed_tasks
            attendance.save()
            
            # Handle multiple file uploads for completed tasks
            completed_files = request.FILES.getlist('completed_attachments')
            for file in completed_files:
                TaskAttachment.objects.create(
                    attendance=attendance,
                    task_type='completed',
                    image=file
                )
            
            messages.success(request, "Check-out recorded successfully with completed tasks.")
            return redirect('dashboard')
        else:
            messages.warning(request, "Invalid action or attendance already completed for today.")
            return redirect('dashboard')

    return render(request, 'attendance/employee/record_attendance.html', {
        'employee': employee,
        'is_checked_in': is_checked_in,
        'attendance': attendance
    })


@login_required
def employee_profile(request):
    try:
        employee = request.user.employee
    except Employee.DoesNotExist:
        messages.error(request, "You are not registered as an employee.")
        return redirect('login')
    
    attendance_records = Attendance.objects.filter(employee=employee).order_by('-date')[:30]
    
    # NEW: Add leave history
    leave_requests = LeaveRequest.objects.filter(employee=employee).order_by('-created_at')[:10]
    leave_stats = {
        'total': LeaveRequest.objects.filter(employee=employee).count(),
        'pending': LeaveRequest.objects.filter(employee=employee, status='Pending').count(),
        'approved': LeaveRequest.objects.filter(employee=employee, status='Approved').count(),
        'rejected': LeaveRequest.objects.filter(employee=employee, status='Rejected').count(),
    }
    
    return render(request, 'attendance/employee/employee_profile.html', {
        'employee': employee,
        'attendance_records': attendance_records,
        'leave_requests': leave_requests,
        'leave_stats': leave_stats,
    })
 
@login_required
@user_passes_test(is_superuser)
def admin_employee_list(request):
    employees = Employee.objects.all()
    return render(request, 'attendance/admin/admin_employee_list.html', {
        'employees': employees
    })

@login_required
@user_passes_test(is_superuser)
def admin_employee_detail(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    attendance_records = Attendance.objects.filter(employee=employee).order_by('-date')[:30]
    
    # NEW: Add leave history
    leave_requests = LeaveRequest.objects.filter(employee=employee).order_by('-created_at')[:10]
    leave_stats = {
        'total': LeaveRequest.objects.filter(employee=employee).count(),
        'pending': LeaveRequest.objects.filter(employee=employee, status='Pending').count(),
        'approved': LeaveRequest.objects.filter(employee=employee, status='Approved').count(),
        'rejected': LeaveRequest.objects.filter(employee=employee, status='Rejected').count(),
    }
    
    return render(request, 'attendance/admin/admin_employee_detail.html', {
        'employee': employee,
        'attendance_records': attendance_records,
        'leave_requests': leave_requests,
        'leave_stats': leave_stats,
    })

@login_required
@user_passes_test(is_superuser)
def admin_bank_info(request):
    employees = Employee.objects.filter(bank_account_number__isnull=False)
    return render(request, 'attendance/admin/admin_bank_info.html', {
        'employees': employees
    })

@login_required
@user_passes_test(is_superuser)
def admin_dashboard(request):
    from .models import LeaveRequest  # ensure import if not present
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
            datetime.combine(attendance.date, time(17, 0)),
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

    # Get latest 10 leave requests
    recent_leave_requests = LeaveRequest.objects.select_related('employee').order_by('-created_at')[:10]

    return render(request, 'attendance/admin/admin_dashboard.html', {
        'employees': employees,
        'attendance_records': attendance_records,
        'working_days': working_days,
        'attendance_summary': attendance_summary,
        'current_month': calendar.month_name[current_month],
        'current_year': current_year,
        'half_day_records': half_day_records,
        'recent_leave_requests': recent_leave_requests,  # <-- NEW
    })

@login_required
@user_passes_test(is_superuser)
def reset_attendance(request):
    if request.method == 'POST':
        Attendance.objects.all().delete()
        messages.success(request, "Attendance records have been reset successfully.")
        return redirect('admin_dashboard')
    return render(request, 'attendance/admin/reset_attendance.html')

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
    
    selected_year = int(request.GET.get('year', current_year))
    selected_month = int(request.GET.get('month', current_month))
    
    try:
        datetime(selected_year, selected_month, 1)
    except ValueError:
        selected_year = current_year
        selected_month = current_month
    
    _, days_in_month = monthrange(selected_year, selected_month)
    month_name = calendar.month_name[selected_month]
    
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
            'days': [{'status': None, 'details': [], 'is_leave': False} for _ in range(days_in_month)]
        }
        attendance_data.append(employee_data)
    
    # Get attendance records
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
                    }],
                    'is_leave': False
                }
    
    # NEW: Mark approved leave days
    first_day = datetime(selected_year, selected_month, 1).date()
    last_day = datetime(selected_year, selected_month, days_in_month).date()
    
    approved_leaves = LeaveRequest.objects.filter(
        status='Approved',
        start_date__lte=last_day,
        end_date__gte=first_day
    ).select_related('employee')
    
    for leave in approved_leaves:
        employee_idx = next((i for i, data in enumerate(attendance_data) if data['employee']['id'] == leave.employee.id), None)
        if employee_idx is not None:
            # Calculate leave days within the month
            leave_start = max(leave.start_date, first_day)
            leave_end = min(leave.end_date, last_day)
            
            current_date = leave_start
            while current_date <= leave_end:
                day_idx = current_date.day - 1
                if 0 <= day_idx < days_in_month:
                    # Only mark as leave if no attendance record exists
                    if not attendance_data[employee_idx]['days'][day_idx]['status']:
                        attendance_data[employee_idx]['days'][day_idx] = {
                            'status': 'Leave',
                            'details': [{
                                'leave_title': leave.title,
                                'leave_remarks': leave.remarks or 'No remarks'
                            }],
                            'is_leave': True
                        }
                current_date += timedelta(days=1)
    
    return render(request, 'attendance/admin/attendance_calendar.html', {
        'attendance_data': attendance_data,
        'current_month_name': month_name,
        'current_year': selected_year,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'today_date': {'year': current_year, 'month': current_month, 'day': current_day},
        'days_in_month': range(1, days_in_month + 1),
        'available_months': available_months
    })

# CHANGED: employee_attendance view to display hours and minutes
@login_required
@user_passes_test(is_superuser)
def attendance_calendar(request):
    employees = Employee.objects.all().order_by('first_name', 'last_name')
    
    today = timezone.now().date()
    current_year = today.year
    current_month = today.month
    current_day = today.day
    
    selected_year = int(request.GET.get('year', current_year))
    selected_month = int(request.GET.get('month', current_month))
    
    try:
        datetime(selected_year, selected_month, 1)
    except ValueError:
        selected_year = current_year
        selected_month = current_month
    
    _, days_in_month = monthrange(selected_year, selected_month)
    month_name = calendar.month_name[selected_month]
    
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
            'days': [{'status': None, 'details': [], 'is_leave': False} for _ in range(days_in_month)]
        }
        attendance_data.append(employee_data)
    
    # Get attendance records
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
                    }],
                    'is_leave': False
                }
    
    # NEW: Mark ONLY approved leave days (only if no Present attendance exists)
    first_day = datetime(selected_year, selected_month, 1).date()
    last_day = datetime(selected_year, selected_month, days_in_month).date()
    
    approved_leaves = LeaveRequest.objects.filter(
        status='Approved',
        start_date__lte=last_day,
        end_date__gte=first_day
    ).select_related('employee')
    
    for leave in approved_leaves:
        employee_idx = next((i for i, data in enumerate(attendance_data) if data['employee']['id'] == leave.employee.id), None)
        if employee_idx is not None:
            # Calculate leave days within the month
            leave_start = max(leave.start_date, first_day)
            leave_end = min(leave.end_date, last_day)
            
            current_date = leave_start
            while current_date <= leave_end:
                day_idx = current_date.day - 1
                if 0 <= day_idx < days_in_month:
                    # Only mark as leave if no Present attendance record exists
                    if attendance_data[employee_idx]['days'][day_idx]['status'] != 'Present':
                        attendance_data[employee_idx]['days'][day_idx] = {
                            'status': None,  # Don't set status, use is_leave flag instead
                            'details': [{
                                'leave_title': leave.title,
                                'leave_remarks': leave.remarks or 'No remarks'
                            }],
                            'is_leave': True
                        }
                current_date += timedelta(days=1)
    
    return render(request, 'attendance/admin/attendance_calendar.html', {
        'attendance_data': attendance_data,
        'current_month_name': month_name,
        'current_year': selected_year,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'today_date': {'year': current_year, 'month': current_month, 'day': current_day},
        'days_in_month': range(1, days_in_month + 1),
        'available_months': available_months
    })

# Leave Request View

@login_required
def leave_history(request):
    employee = request.user.employee
    leaves = LeaveRequest.objects.filter(employee=employee).order_by('-created_at')
    return render(request, 'attendance/leave_history.html', {
        'leaves': leaves
    })

@login_required
def request_leave(request):
    employee = request.user.employee
    if request.method == 'POST':
        title = request.POST.get('title')
        remarks = request.POST.get('remarks')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        if not (title and start_date and end_date):
            messages.error(request, 'Title, start date, and end date are required.')
        else:
            LeaveRequest.objects.create(
                employee=employee,
                title=title,
                remarks=remarks,
                start_date=start_date,
                end_date=end_date,
                status='Pending'
            )
            messages.success(request, 'Leave request submitted successfully.')
            return redirect('leave_history')
    return render(request, 'attendance/request_leave.html')

# Admin Leave Management Views

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_leave_requests(request):
    leave_requests = LeaveRequest.objects.all().order_by('-created_at')
    return render(request, 'attendance/admin/admin_leave_requests.html', {
        'leave_requests': leave_requests
    })
login_required
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

    return render(request, 'attendance/employee/employee_attendance.html', {
        'employee': employee,
        'monthly_records': sorted_months
    })

@login_required
@user_passes_test(lambda u: u.is_superuser)
def approve_reject_leave(request, leave_id, action):
    leave = get_object_or_404(LeaveRequest, id=leave_id)
    if action == 'approve':
        leave.status = 'Approved'
    elif action == 'reject':
        leave.status = 'Rejected'
    leave.save()
    messages.success(request, f'Leave request {action}d.')
    return redirect('admin_leave_requests')



@login_required
@user_passes_test(is_superuser)
def admin_notices(request):
    """Display all notices for admin management"""
    notices = Notice.objects.all().order_by('-published_at')

    # Compute stats in Python, not in template
    total_notices = notices.count()
    active_count = notices.filter(is_active=True).count()
    inactive_count = notices.filter(is_active=False).count()
    urgent_count = notices.filter(priority='urgent').count()

    return render(request, 'attendance/notice/admin_notices.html', {
        'notices': notices,
        'total_notices': total_notices,
        'active_count': active_count,
        'inactive_count': inactive_count,
        'urgent_count': urgent_count,
    })

@login_required
@user_passes_test(is_superuser)
def create_notice(request):
    """Create a new notice"""
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        priority = request.POST.get('priority', 'medium')
        is_active = request.POST.get('is_active') == 'on'
        
        if not title or not description:
            messages.error(request, 'Title and description are required.')
            return redirect('create_notice')
        
        Notice.objects.create(
            title=title,
            description=description,
            priority=priority,
            is_active=is_active,
            created_by=request.user
        )
        messages.success(request, 'Notice created successfully.')
        return redirect('admin_notices')
    
    return render(request, 'attendance/notice/create_notice.html')

@login_required
@user_passes_test(is_superuser)
def edit_notice(request, notice_id):
    """Edit an existing notice"""
    notice = get_object_or_404(Notice, id=notice_id)
    
    if request.method == 'POST':
        notice.title = request.POST.get('title')
        notice.description = request.POST.get('description')
        notice.priority = request.POST.get('priority', 'medium')
        notice.is_active = request.POST.get('is_active') == 'on'
        
        if not notice.title or not notice.description:
            messages.error(request, 'Title and description are required.')
            return redirect('edit_notice', notice_id=notice_id)
        
        notice.save()
        messages.success(request, 'Notice updated successfully.')
        return redirect('admin_notices')
    
    return render(request, 'attendance/notice/edit_notice.html', {
        'notice': notice
    })

@login_required
@user_passes_test(is_superuser)
def toggle_notice(request, notice_id):
    """Toggle notice active status"""
    notice = get_object_or_404(Notice, id=notice_id)
    notice.is_active = not notice.is_active
    notice.save()
    
    status = "activated" if notice.is_active else "deactivated"
    messages.success(request, f'Notice "{notice.title}" has been {status}.')
    return redirect('admin_notices')

@login_required
@user_passes_test(is_superuser)
def delete_notice(request, notice_id):
    """Delete a notice"""
    notice = get_object_or_404(Notice, id=notice_id)
    
    if request.method == 'POST':
        notice_title = notice.title
        notice.delete()
        messages.success(request, f'Notice "{notice_title}" has been deleted.')
        return redirect('admin_notices')
    
    return render(request, 'attendance/notice/delete_notice.html', {
        'notice': notice
    })

# Salary Calculator View Admin
@login_required
@user_passes_test(is_superuser)
def salary_calculator(request):
    employees = Employee.objects.all().order_by('first_name', 'last_name')
    results = []
    selected_employee = None

    if request.method == 'POST':
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')
        employee_id = request.POST.get('employee_id')

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

            if start_date > end_date:
                messages.error(request, "Start date cannot be after end date.")
                return render(request, 'attendance/admin/salary_calculator.html', {'employees': employees})

            # Calculate total days in the date range
            total_days_in_range = (end_date - start_date).days + 1

            # Filter employees if specific employee selected
            if employee_id and employee_id != 'all':
                employees_to_calculate = Employee.objects.filter(id=employee_id)
                selected_employee = get_object_or_404(Employee, id=employee_id)
            else:
                employees_to_calculate = employees

            for emp in employees_to_calculate:
                if emp.monthly_salary <= 0:
                    continue  # Skip if no salary set

                # Calculate daily rate based on 30-day month standard
                daily_rate = emp.monthly_salary / Decimal('30')

                # Get all dates in the range
                date_range = []
                current_date = start_date
                while current_date <= end_date:
                    date_range.append(current_date)
                    current_date += timedelta(days=1)

                # Count absent days (days without Present status and without approved leave)
                absent_days = 0
                present_days = 0
                approved_leave_days = 0

                for single_date in date_range:
                    # Check if there's an attendance record
                    attendance = Attendance.objects.filter(
                        employee=emp,
                        date=single_date
                    ).first()

                    # Check if there's an approved leave for this date
                    has_approved_leave = LeaveRequest.objects.filter(
                        employee=emp,
                        status='Approved',
                        start_date__lte=single_date,
                        end_date__gte=single_date
                    ).exists()

                    if has_approved_leave:
                        approved_leave_days += 1
                    elif attendance and attendance.status == 'Present':
                        present_days += 1
                    else:
                        # No attendance and no approved leave = absent
                        absent_days += 1

                # Calculate payable days: total days minus absent days
                payable_days = total_days_in_range - absent_days
                
                # Calculate gross salary
                gross_salary = daily_rate * Decimal(payable_days)

                # Calculate deductions (optional - for absent days)
                deduction = daily_rate * Decimal(absent_days)

                results.append({
                    'employee': emp,
                    'daily_rate': daily_rate,
                    'total_days': total_days_in_range,
                    'present_days': present_days,
                    'approved_leave_days': approved_leave_days,
                    'absent_days': absent_days,
                    'payable_days': payable_days,
                    'gross_salary': gross_salary.quantize(Decimal('0.01')),
                    'deduction': deduction.quantize(Decimal('0.01')),
                    'start_date': start_date,
                    'end_date': end_date,
                })

        except ValueError:
            messages.error(request, "Invalid date format.")
        except Employee.DoesNotExist:
            messages.error(request, "Employee not found.")

    # Calculate totals for summary cards
    total_gross_salary = sum(r['gross_salary'] for r in results)
    total_present_days = sum(r['present_days'] for r in results)
    total_absent_days = sum(r['absent_days'] for r in results)
    total_leave_days = sum(r['approved_leave_days'] for r in results)

    return render(request, 'attendance/admin/salary_calculator.html', {
        'employees': employees,
        'results': results,
        'start_date': request.POST.get('start_date') if request.method == 'POST' else '',
        'end_date': request.POST.get('end_date') if request.method == 'POST' else '',
        'selected_employee': selected_employee,
        'selected_employee_id': request.POST.get('employee_id') if request.method == 'POST' else 'all',
        'total_gross_salary': total_gross_salary,
        'total_present_days': total_present_days,
        'total_absent_days': total_absent_days,
        'total_leave_days': total_leave_days,
    })

# Task Management Views
@login_required
def task_detail(request, attendance_id):
    """View to show task details with attachments"""
    attendance = get_object_or_404(Attendance, id=attendance_id)
    
    # Check if user is authorized (employee viewing own tasks or admin)
    if not (request.user.is_superuser or attendance.employee.user == request.user):
        messages.error(request, "You don't have permission to view this.")
        return redirect('dashboard')
    
    todo_attachments = attendance.get_todo_attachments()
    completed_attachments = attendance.get_completed_attachments()
    
    return render(request, 'attendance/tasks/task_detail.html', {
        'attendance': attendance,
        'todo_attachments': todo_attachments,
        'completed_attachments': completed_attachments,
    })


# Admin view to see all employee tasks for today
@login_required
@user_passes_test(is_superuser)
def admin_daily_tasks(request):
    """Admin view to see all employees' tasks for today"""
    today = timezone.now().date()
    selected_date = request.GET.get('date', today.strftime('%Y-%m-%d'))
    
    try:
        selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    except ValueError:
        selected_date = today
    
    # Get all attendance records for selected date
    attendances = Attendance.objects.filter(
        date=selected_date
    ).select_related('employee').prefetch_related('task_attachments')
    
    # Prepare task data
    task_data = []
    for attendance in attendances:
        task_data.append({
            'employee': attendance.employee,
            'attendance': attendance,
            'todo_tasks': attendance.todo_tasks,
            'completed_tasks': attendance.completed_tasks,
            'todo_attachments': attendance.get_todo_attachments(),
            'completed_attachments': attendance.get_completed_attachments(),
            'check_in': attendance.check_in,
            'check_out': attendance.check_out,
        })
    
    return render(request, 'attendance/tasks/admin_daily_tasks.html', {
        'task_data': task_data,
        'selected_date': selected_date,
        'today': today,
    })