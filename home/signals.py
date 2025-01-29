from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Student, AttendanceRecord
import datetime

@receiver(post_save, sender=Student)
def create_or_update_attendance(sender, instance, created, **kwargs):
    today = datetime.date.today()

    if created:
        AttendanceRecord.objects.create(
            student=instance,
            date=today,
            status=instance.status  
        )
    else:
        attendance_record, created = AttendanceRecord.objects.get_or_create(
            student=instance,
            date=today,
            defaults={'status': instance.status}
        )
        if not created and attendance_record.status != instance.status:
            attendance_record.status = instance.status
            attendance_record.save()
