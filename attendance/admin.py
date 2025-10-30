from django.contrib import admin
from .models import Department, Employee, Attendance, LeaveRequest

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'first_name', 'last_name', 'department', 'email')
    search_fields = ('employee_id', 'first_name', 'last_name', 'email')
    list_filter = ('department',)

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'check_in', 'check_out', 'hours_worked', 'status')
    list_filter = ('date', 'status', 'employee')
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_id')

@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('employee', 'title', 'start_date', 'end_date', 'status', 'created_at')
    list_filter = ('status', 'start_date', 'end_date', 'employee')
    search_fields = ('employee__first_name', 'employee__last_name', 'title', 'remarks')