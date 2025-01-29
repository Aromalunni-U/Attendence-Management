import os
import cv2
import time
import base64 
import pickle
# import pandas as pd
from datetime import datetime
from keras_facenet import FaceNet
from yoloface import face_analysis
from django.contrib import messages
from django.contrib.auth import  login
from scipy.spatial.distance import cosine
from .models import Student,Stack,Faculty    
from django.shortcuts import render,redirect
from django.core.files.base import ContentFile
from django.shortcuts import render, get_object_or_404
from django.http import StreamingHttpResponse



# index------------------------------------------------

def index(request):
    return render(request,"index.html")

# sheet------------------------------------------------

def sheet(request):
    return render(request,"sheet.html")

# add student------------------------------------------


def add_student(request):
    if request.method == "POST":
        data = request.POST
        first_name = data.get("first_name").strip().capitalize()
        last_name = data.get("last_name").strip()
        gender = data.get("gender")
        stack = data.get("stack")
        phone = data.get("phone")
        email = data.get("email").strip().lower()
        info = data.get("info").strip()
        join_date = data.get("join_date")
        image = data.get("image") 

        if Student.objects.filter(email=email).exists():
            messages.error(request, 'This email is already registered.')
            return redirect('add_student')

        stack = Stack.objects.get(id=stack)
        
        if image: 
            format, imgstr = image.split(';base64,') 
            ext = format.split('/')[-1] 
            image_name = f"{first_name}{last_name}.jpg"
            image = ContentFile(base64.b64decode(imgstr), name=image_name)

        
        Student.objects.create(
            first_name=first_name,
            last_name=last_name,
            gender=gender,
            stack=stack,
            phone=phone,
            email=email,
            info=info,
            join_date=join_date,
            image=image            
        )
        messages.success(request, 'Student added successfully')
      

        return redirect('add_student')

    context = {
        'stacks': Stack.objects.all(),
    }
    return render(request, "add_student.html", context)



# __________________________________________________________________________


embedder = FaceNet()
face = face_analysis()

students_pickle_path = os.path.join('enrollment', 'students')
faculty_pickle_path = os.path.join('enrollment', 'faculty')

def recognize_face(face_embedding, dir_path):
    min_distance = float('inf')
    recognized_person = "UNKNOWN"
    recognition_accuracy = 0

    for file in os.listdir(dir_path):
        if file.endswith('.pkl'):  
            stored_embeddings = pickle.load(open(os.path.join(dir_path, file), 'rb'))
            for stored_embedding in stored_embeddings:
                distance = cosine(face_embedding, stored_embedding)
                accuracy = (1 - distance) * 100  

                if distance < min_distance:
                    min_distance = distance
                    recognized_person = file.split('.')[0] 
                    recognition_accuracy = accuracy

    if min_distance < 0.6:  
        return recognized_person, recognition_accuracy
    else:
        return "UNKNOWN", 0

def gen(request):
    cap = cv2.VideoCapture(1)
    
    duration = int(request.GET.get('duration', 0))

    duration_seconds = duration / 1000

    start_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        elapsed_time = time.time() - start_time
        print(f"Elapsed time: {elapsed_time:.2f} seconds")

        if elapsed_time >= duration_seconds:
            break  

        _, boxes, _ = face.face_detection(frame_arr=frame, frame_status=True, model='tiny')

        if len(boxes) > 0:
            for box in boxes:
                x, y, w, h = box
                face_crop = frame[y:y + w, x:x + h]

                if face_crop is not None and face_crop.size > 0:
                    face_resized = cv2.resize(face_crop, (160, 160))

                    face_embedding = embedder.embeddings([face_resized])[0]
                    hub_id, accuracy = recognize_face(face_embedding, students_pickle_path)  

                    if hub_id != "UNKNOWN" and accuracy > 72:
                        try:
                            student = get_object_or_404(Student, hub_id=hub_id) 
                            student.status = "Present"
                            student.save()
                        except Student.DoesNotExist:
                            pass

                        cv2.putText(frame, f"{hub_id} ({accuracy:.2f}%)", (x, y - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
                        cv2.rectangle(frame, (x, y), (x + h, y + w), (0, 255, 0), 2)

        ret, jpeg = cv2.imencode('.jpg', frame)
        if not ret:
            break
        frame_bytes = jpeg.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n\r\n')

    cap.release()

def video_stream(request):
    return StreamingHttpResponse(gen(request), content_type='multipart/x-mixed-replace; boundary=frame')

def attendance(request):
    if request.method == "POST":
        selected_time = int(request.POST.get("time", 1))
        duration = selected_time * 60 
        request.session['duration'] = duration
        
        return render(request, 'index.html', {'duration': duration})

    return render(request, 'index.html')
