from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from nepali_datetime import date as nepali_date

class Department(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=10, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    email = models.EmailField(unique=True)
    address = models.TextField(blank=True, null=True)
    position = models.CharField(max_length=100, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    dob_nepali = models.CharField(max_length=10, blank=True, null=True)  # Format: YYYY/MM/DD in BS
    bank_account_number = models.CharField(max_length=50, blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    bank_account_holder_name = models.CharField(max_length=100, blank=True, null=True)
    photo = models.ImageField(upload_to='employee_photos/', blank=True, null=True)


    def save(self, *args, **kwargs):
        if self.dob and not self.dob_nepali:
            nepali_dob = nepali_date.from_datetime(self.dob)
            self.dob_nepali = nepali_dob.strftime('%Y/%m/%d')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_id})"

class Attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)
    hours_worked = models.FloatField(null=True, blank=True)
    date = models.DateField(default=timezone.now)
    comments = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, default='Present', choices=[
        ('Present', 'Present'),
        ('Absent', 'Absent')
    ])

    def save(self, *args, **kwargs):
        if self.check_out and self.check_in:
            delta = self.check_out - self.check_in
            self.hours_worked = delta.total_seconds() / 3600
            self.status = 'Present'
        else:
            self.hours_worked = None
            if not self.check_in:
                self.status = 'Absent'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee} - {self.date} ({self.status})"

class AbsentEmployeeManager:
    @staticmethod
    def mark_absent_for_day(target_date=None):
        if target_date is None:
            target_date = timezone.now().date()
        
        employees = Employee.objects.all()
        for employee in employees:
            attendance_exists = Attendance.objects.filter(
                employee=employee,
                date=target_date
            ).exists()
            if not attendance_exists:
                Attendance.objects.create(
                    employee=employee,
                    date=target_date,
                    status='Absent'
                )