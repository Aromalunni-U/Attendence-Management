import os
import cv2
import pickle
import datetime
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Student, Faculty, AttendanceRecord
from mtcnn import MTCNN
from keras_facenet import FaceNet

mtcnn = MTCNN()
embedder = FaceNet()

pickle_dir = 'enrollment'
student_pickle_dir = os.path.join(pickle_dir, 'students')
faculty_pickle_dir = os.path.join(pickle_dir, 'faculty')

os.makedirs(student_pickle_dir, exist_ok=True)
os.makedirs(faculty_pickle_dir, exist_ok=True)

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
    if instance.image: 
        image_path = instance.image.path
        hub_id = instance.hub_id
        embeddings = preprocess_and_extract_embeddings(image_path)
        save_embeddings(embeddings, hub_id, is_student=True)

@receiver(post_save, sender=Faculty)
def generate_embeddings_for_faculty(sender, instance, created, **kwargs):
    if instance.image: 
        image_path = instance.image.path
        email_prefix = instance.user.email.split('@')[0]  
        embeddings = preprocess_and_extract_embeddings(image_path)
        save_embeddings(embeddings, email_prefix, is_student=False)

@receiver(post_save, sender=Student)
def create_or_update_student_attendance(sender, instance, created, **kwargs):
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
