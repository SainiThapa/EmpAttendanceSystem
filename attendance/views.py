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

    if request.method == 'POST':
        today = timezone.now().date()
        comments = request.POST.get('comments', '')
        attendance, created = Attendance.objects.get_or_create(
            employee=employee,
            date=today,
            defaults={'check_in': timezone.now(), 'comments': comments}
        )
        if not created and not attendance.check_out:
            attendance.check_out = timezone.now()
            attendance.comments = comments
            attendance.save()
            messages.success(request, "Check-out recorded successfully.")
        elif not created and attendance.check_out:
            messages.warning(request, "Attendance already completed for today.")
        else:
            messages.success(request, "Check-in recorded successfully.")
        return redirect('dashboard')
    return render(request, 'attendance/record_attendance.html', {'employee': employee})
