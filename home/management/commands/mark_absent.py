from django.core.management.base import BaseCommand
from home.models import Student, AttendanceRecord
import datetime

class Command(BaseCommand):
    help = "Mark all students as absent or inactive for today's date in AttendanceRecord"

    def handle(self, *args, **kwargs):
        today = datetime.date.today()

        if today.weekday() < 5:  
            students = Student.objects.exclude(status__in=['Placed', 'Resigned']) 

            for student in students:
                if student.is_active:
                    status = 'Absent'
                else:
                    status = 'Inactive'

                if not AttendanceRecord.objects.filter(student=student, date=today).exists():
                    AttendanceRecord.objects.create(student=student, date=today, status=status)
                else:
                    AttendanceRecord.objects.filter(student=student, date=today).update(status=status)
                
                student.status = status  
                student.save()
            
            self.stdout.write("Attendance records for all students updated.")

