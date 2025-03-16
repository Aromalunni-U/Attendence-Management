import os
import cv2
import pickle
import datetime
from mtcnn import MTCNN
from django.db import models
from keras_facenet import FaceNet
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.models import User

mtcnn = MTCNN()
embedder = FaceNet()

pickle_dir = 'enrollment'

student_pickle_dir = os.path.join(pickle_dir, 'students') 
faculty_pickle_dir = os.path.join(pickle_dir, 'faculty') 

os.makedirs(student_pickle_dir, exist_ok=True)
os.makedirs(faculty_pickle_dir, exist_ok=True)
# Stack---------------------------------------------------------

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

# Student--------------------------------------------------------

class Student(models.Model):
    hub_id = models.CharField(max_length=20, unique=True, blank=True)
    first_name = models.CharField(max_length=70)
    last_name = models.CharField(max_length=70)
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    
    stack = models.ForeignKey(Stack, on_delete=models.CASCADE, null=True, blank=True)
    phone = models.BigIntegerField()
    email = models.EmailField(unique=True)
    info = models.TextField(null=True, blank=True)

    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Interview', 'Interview'),
        ('Inactive','Inactive'),
        ('Placed','Placed'),
        ('Resigned','Resigned')
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Absent')
    join_date = models.DateField(default=datetime.date.today)
    is_active = models.BooleanField(default=True) 
    image = models.ImageField(upload_to="student_images/")

    def save(self, *args, **kwargs):
        if not self.hub_id: 
            last_student = Student.objects.order_by('-id').first()
            last_id = int(last_student.hub_id.replace('hub', '')) if last_student and last_student.hub_id else 0
            self.hub_id = f'hub{last_id + 1}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

# Attendance ----------------------------------------------------------

class AttendanceRecord(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField(default=datetime.date.today)
    status = models.CharField(max_length=10, choices=Student.STATUS_CHOICES, default='Absent')

    class Meta:
        unique_together = ('student', 'date')

    def __str__(self):
        return f'{self.student} - {self.date} - {self.status}'
    
# ----------------------------------------------------------------------

def preprocess_and_extract_embeddings(image_path):
    embeddings = []
    if image_path.endswith(('.jpg', '.jpeg', '.png')):
        image = cv2.imread(image_path)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        detections = mtcnn.detect_faces(rgb_image)

        if detections:
            for detection in detections:
                x, y, w, h = detection['box']
                face = rgb_image[y:y + h, x:x + w]
                face_resized = cv2.resize(face, (160, 160))
                embedding = embedder.embeddings([face_resized])[0]
                embeddings.append(embedding)
    
    return embeddings

def save_embeddings(embeddings, file_name, is_student):
    folder = student_pickle_dir if is_student else faculty_pickle_dir
    os.makedirs(folder, exist_ok=True)
    file_path = os.path.join(folder, f'{file_name}.pkl')  

    with open(file_path, 'wb') as f:
        pickle.dump(embeddings, f)

@receiver(post_save, sender=Student)
def generate_embeddings_for_student(sender, instance, created, **kwargs):
    if created: 
        image_path = instance.image.path
        hub_id = instance.hub_id
        embeddings = preprocess_and_extract_embeddings(image_path)
        save_embeddings(embeddings, hub_id, is_student=True)

@receiver(post_save, sender=Faculty)
def generate_embeddings_for_faculty(sender, instance, created, **kwargs):
    if created: 
        image_path = instance.image.path
        email_prefix = instance.user.email.split('@')[0]  
        embeddings = preprocess_and_extract_embeddings(image_path)
        save_embeddings(embeddings, email_prefix, is_student=False)