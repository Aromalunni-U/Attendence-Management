import datetime
from django.db import models
from django.contrib.auth.models import User



# stack---------------------------------------------------------

class Stack(models.Model):
    stack_name = models.CharField(max_length=20)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.stack_name
    

# Faculty--------------------------------------------------------

class Faculty(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=70)
    last_name = models.CharField(max_length=70)  
    join_date = models.DateField()  
    image = models.ImageField(upload_to='faculty_faces/') 

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


# student--------------------------------------------------------

class Student(models.Model):
    first_name = models.CharField(max_length=70)
    last_name = models.CharField(max_length=70)
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    
    stack = models.ForeignKey(Stack, on_delete=models.CASCADE,null=True,blank=True)

    MONTH_CHOICES = [
        ('January', 'January'),
        ('February', 'February'),
        ('March', 'March'),
        ('April', 'April'),
        ('May', 'May'),
        ('June', 'June'),
        ('July', 'July'),
        ('August', 'August'),
        ('September', 'September'),
        ('October', 'October'),
        ('November', 'November'),
        ('December', 'December'),
    ]
    batch = models.CharField(max_length=20, choices=MONTH_CHOICES)
    phone = models.BigIntegerField()
    email = models.EmailField(unique=True)
    info = models.TextField(null=True, blank=True)

    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Interview', 'Interview'),
        ('Leave', 'Leave'),
    ]
    present = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Absent')
    join_date = models.DateField(default=datetime.date.today)
    is_active = models.BooleanField(default=True) 
    image = models.ImageField(upload_to="media")

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

# attendence  --------------------------------------------------------------------------
   
class AttendanceRecord(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField(default=datetime.date.today)
    status = models.CharField(max_length=10, choices=Student.STATUS_CHOICES, default='Absent')

    class Meta:
        unique_together = ('student', 'date')

    def __str__(self):
        return f'{self.student} - {self.date} - {self.status}'