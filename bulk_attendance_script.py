import os
import django
from datetime import datetime, time

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Attendance_Emp.settings') 
django.setup()

from django.utils import timezone
from attendance.models import Employee, Attendance

def create_bulk_attendance():
    """
    Create attendance records for all employees
    for dates: Nov 11, 12, 13 (2025)
    Time: 9:00 AM to 5:00 PM
    """
    
    # Define dates (Nov 11-13, 2025)
    dates = [
        datetime(2025, 11, 11).date(),
        datetime(2025, 11, 12).date(),
        datetime(2025, 11, 13).date(),
    ]
    
    # Get all employees
    employees = Employee.objects.all()
    
    if not employees.exists():
        print("❌ No employees found in the database!")
        return
    
    print(f"📋 Found {employees.count()} employees")
    print(f"📅 Creating attendance for dates: {', '.join(str(d) for d in dates)}")
    print(f"⏰ Time: 09:00 - 17:00")
    print("-" * 60)
    
    created_count = 0
    skipped_count = 0
    
    for employee in employees:
        for date in dates:
            # Check if attendance already exists
            existing = Attendance.objects.filter(
                employee=employee,
                date=date
            ).first()
            
            if existing:
                print(f"⏭️  Skipped: {employee.first_name} {employee.last_name} - {date} (already exists)")
                skipped_count += 1
                continue
            
            # Create check-in time (9:00 AM)
            check_in_datetime = timezone.make_aware(
                datetime.combine(date, time(9, 0)),
                timezone.get_current_timezone()
            )
            
            # Create check-out time (5:00 PM)
            check_out_datetime = timezone.make_aware(
                datetime.combine(date, time(17, 0)),
                timezone.get_current_timezone()
            )
            
            # Create attendance record
            attendance = Attendance.objects.create(
                employee=employee,
                date=date,
                check_in=check_in_datetime,
                check_out=check_out_datetime,
                status='Present',
                comments='Bulk attendance record'
            )
            
            print(f"✅ Created: {employee.first_name} {employee.last_name} - {date}")
            created_count += 1
    
    print("-" * 60)
    print(f"✨ Summary:")
    print(f"   ✅ Created: {created_count} records")
    print(f"   ⏭️  Skipped: {skipped_count} records")
    print(f"   📊 Total: {created_count + skipped_count} records processed")
    print(f"   👥 Employees: {employees.count()}")
    print(f"   📅 Dates: {len(dates)}")

if __name__ == '__main__':
    try:
        create_bulk_attendance()
        print("\n🎉 Script completed successfully!")
    except Exception as e:
        print(f"\n❌ Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
