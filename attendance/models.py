from django.db import models
from django.utils import timezone

class Department(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Employee(models.Model):
    employee_id = models.CharField(max_length=10, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    email = models.EmailField(unique=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_id})"

class Attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    check_in = models.DateTimeField()
    check_out = models.DateTimeField(null=True, blank=True)
    hours_worked = models.FloatField(null=True, blank=True)
    date = models.DateField(default=timezone.now)

    def save(self, *args, **kwargs):
        if self.check_out and self.check_in:
            # Calculate hours worked
            delta = self.check_out - self.check_in
            self.hours_worked = delta.total_seconds() / 3600  # Convert to hours
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee} - {self.date}"