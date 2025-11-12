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

    monthly_salary = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00,
        help_text="Monthly base salary in NPR")

    def save(self, *args, **kwargs):
        if self.dob and not self.dob_nepali:
            nepali_dob = nepali_date.from_datetime(self.dob)
            self.dob_nepali = nepali_dob.strftime('%Y/%m/%d')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_id})"

class Attendance(models.Model):
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE)
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)
    hours_worked = models.FloatField(null=True, blank=True)
    date = models.DateField(default=timezone.now)
    
    # OLD comment field (keep for backward compatibility)
    comments = models.TextField(blank=True, null=True)
    
    # NEW task-related fields
    todo_tasks = models.TextField(blank=True, null=True, help_text="Tasks to do for the day (check-in)")
    completed_tasks = models.TextField(blank=True, null=True, help_text="Tasks completed (check-out)")
    
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
    
    def get_todo_attachments(self):
        """Get all to-do task attachments"""
        return self.task_attachments.filter(task_type='todo')
    
    def get_completed_attachments(self):
        """Get all completed task attachments"""
        return self.task_attachments.filter(task_type='completed')
    
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

class TaskAttachment(models.Model):
    """Model to store multiple attachments for tasks"""
    TASK_TYPE_CHOICES = [
        ('todo', 'To-Do'),
        ('completed', 'Completed'),
    ]
    
    attendance = models.ForeignKey('Attendance', on_delete=models.CASCADE, related_name='task_attachments')
    task_type = models.CharField(max_length=10, choices=TASK_TYPE_CHOICES)
    image = models.ImageField(upload_to='task_attachments/%Y/%m/%d/')
    caption = models.CharField(max_length=200, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.task_type} - {self.attendance.employee} - {self.uploaded_at}"
    
    class Meta:
        ordering = ['-uploaded_at']



class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="leave_requests")
    title = models.CharField(max_length=100)
    remarks = models.TextField(blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee} ({self.title}) [{self.start_date} to {self.end_date}] - {self.status}"
    

class Notice(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='notices_created')
    
    class Meta:
        ordering = ['-published_at', '-created_at']
    
    def __str__(self):
        return f"{self.title} - {'Active' if self.is_active else 'Inactive'}"
    
    @property
    def is_new(self):
        """Check if notice was published within last 24 hours"""
        return (timezone.now() - self.published_at).days < 1
