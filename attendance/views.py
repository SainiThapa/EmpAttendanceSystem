from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Employee, Attendance

def is_staff_or_superuser(user):
    return user.is_staff or user.is_superuser

@login_required
def employee_list(request):
    employees = Employee.objects.all()
    return render(request, 'attendance/employee_list.html', {'employees': employees})

@login_required
def attendance_history(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    attendance_records = Attendance.objects.filter(employee=employee).order_by('-date')
    return render(request, 'attendance/attendance_history.html', {
        'employee': employee,
        'attendance_records': attendance_records
    })

@login_required
@user_passes_test(is_staff_or_superuser)
def check_in_out(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    if request.method == 'POST':
        today = timezone.now().date()
        attendance, created = Attendance.objects.get_or_create(
            employee=employee,
            date=today,
            defaults={'check_in': timezone.now()}
        )
        if not created and not attendance.check_out:
            attendance.check_out = timezone.now()
            attendance.save()
            messages.success(request, f"Check-out recorded for {employee}.")
        elif not created and attendance.check_out:
            messages.warning(request, f"Attendance already completed for {employee} today.")
        else:
            messages.success(request, f"Check-in recorded for {employee}.")
        return redirect('attendance_history', employee_id=employee.id)
    return render(request, 'attendance/check_in_out.html', {'employee': employee})