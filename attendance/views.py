from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Employee, Attendance

@login_required
def dashboard(request):
    try:
        employee = request.user.employee
    except Employee.DoesNotExist:
        messages.error(request, "You are not registered as an employee.")
        return redirect('login')

    today = timezone.now().date()
    attendance = Attendance.objects.filter(employee=employee, date=today).first()
    history = Attendance.objects.filter(employee=employee).exclude(date=today).order_by('-date')

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
    is_checked_in = attendance and not attendance.check_out  # True if checked in but not checked out

    if request.method == 'POST':
        comments = request.POST.get('comments', '')
        if not attendance:
            # Check-in
            Attendance.objects.create(
                employee=employee,
                check_in=timezone.now(),
                date=today,
                comments=comments
            )
            messages.success(request, "Check-in recorded successfully.")
        elif is_checked_in:
            # Check-out
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