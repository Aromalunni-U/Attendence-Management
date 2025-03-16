import os
import cv2
import time
import base64 
import pickle
import pandas as pd
from datetime import datetime
from datetime import date
from django.db.models import Q
from datetime import timedelta
from keras_facenet import FaceNet
from yoloface import face_analysis
from django.contrib import messages
from django.contrib.auth import  login
from scipy.spatial.distance import cosine
from .models import Student,Stack,AttendanceRecord,Faculty
from django.shortcuts import render,redirect
from django.core.files.base import ContentFile
from django.shortcuts import render, get_object_or_404
from django.http import StreamingHttpResponse
from django.http import HttpResponse



# index------------------------------------------------

def index(request):
    return render(request,"index.html")


def custom_404_view(request, exception):
    return render(request, '404.html', status=404)

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
    cap = cv2.VideoCapture(0)
    
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

                        cv2.putText(frame, f"Attendance Marked: {student.first_name} {student.last_name}", (20,50),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
                        cv2.rectangle(frame, (x, y), (x + h, y + w), (255, 255, 255), 2)

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

# faculty login --------------------------------------------------

def faculty_login(request):
    cap = cv2.VideoCapture(0)
    start_time = time.time()
    duration = 30  

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        _, boxes, _ = face.face_detection(frame_arr=frame, frame_status=True, model='tiny')

        if len(boxes) > 0:
            for box in boxes:
                x, y, w, h = box
                face_crop = frame[y:y + w, x:x + h]

                if face_crop is not None and face_crop.size > 0:
                    face_resized = cv2.resize(face_crop, (160, 160))

                    face_embedding = embedder.embeddings([face_resized])[0]
                    
                    person, accuracy = recognize_face(face_embedding,faculty_pickle_path)
                    print('Accuracy:', accuracy)
                    print(f"Recognized: {person} with accuracy: {accuracy:.2f}%")

                    if person != "UNKNOWN" and accuracy > 72:
                        email = f"{person}@gmail.com" 
                        
                        try:
                            faculty = get_object_or_404(Faculty, user__email__iexact=email)
                            
                            user = faculty.user
                            if user.is_superuser or user.is_staff:
                                login(request, user)
                                cap.release()
                                cv2.destroyAllWindows()
                                messages.success(request,f"Welcome, {faculty.first_name} {faculty.last_name}!")                          
                                return redirect('admin_dashboard')  

                        except Faculty.DoesNotExist:
                            print(f"No faculty found with the email {email}")

                        cv2.putText(frame, f"{person} ({accuracy:.2f}%)", (x, y - 10), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
                        cv2.rectangle(frame, (x, y), (x + h, y + w), (0, 255, 0), 2)

        cv2.imshow("Face Recognition", frame)

        if cv2.waitKey(1) & 0xFF == 27 or (time.time() - start_time) > duration:
            break

    cap.release()
    cv2.destroyAllWindows()
    return render(request, "index.html")


# sheet -------------------------------------------------------------------------------------------

def generate_excel(attendance_list, all_dates, search, selected_month, status_type):
    sheet_name = "Attendance" if status_type != "placed_resigned" else "Placed & Resigned"
    filename = f"attendance_{selected_month}.xlsx" if status_type != "placed_resigned" else f"placed_resigned_{selected_month}.xlsx"

    data = []
    headers = ['No.', 'Student', 'Stack'] + [date.strftime('%d-%m-%Y') for date in all_dates] + ['Total Present', 'Total Absent',"Total Interview"]

    for idx, attendance in enumerate(attendance_list, start=1):
        row = [idx, f"{attendance['student'].first_name} {attendance['student'].last_name}", attendance['stack']]
        row.extend(attendance['dates'])
        row.append(attendance['total_present'])
        row.append(attendance['total_absent'])
        row.append(attendance['total_interview'])
        data.append(row)

    df = pd.DataFrame(data, columns=headers)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename={filename}'
    
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)

    return response


#----

def sheet(request):
    selected_month = request.GET.get('month', datetime.now().strftime('%Y-%m'))
    search = request.GET.get('search', '')
    download = request.GET.get('download', '')
    status_type = request.GET.get('status_type', '')

    try:
        start_date = datetime.strptime(selected_month, "%Y-%m")
    except ValueError:
        start_date = datetime.now().replace(day=1)
    end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    attendance_records = AttendanceRecord.objects.filter(date__range=(start_date, end_date))

    if status_type == 'placed_resigned':
        attendance_records = attendance_records.filter(student__status__in=['Placed', 'Resigned'])
    else:
        attendance_records = attendance_records.exclude(student__status__in=['Placed', 'Resigned'])

    if search:
        attendance_records = attendance_records.filter(student__first_name__icontains=search)

    all_dates = sorted(set(attendance_records.values_list('date', flat=True)))

    attendance_list = []
    for student in attendance_records.values('student').distinct():
        student_attendance = attendance_records.filter(student=student['student'])
        statuses = []
        total_present = 0
        total_absent = 0
        total_interview = 0

        for date in all_dates:
            record = student_attendance.filter(date=date).first()
            if record:
                statuses.append(record.status)
                if record.status == "Present":
                    total_present += 1
                elif record.status == "Absent":
                    total_absent += 1
                elif record.status == "Interview":
                    total_interview += 1
            else:
                statuses.append("N/A")

        attendance_list.append({
            "student": student_attendance.first().student,
            "stack": student_attendance.first().student.stack.stack_name,
            "dates": statuses,
            "total_present": total_present,
            "total_absent": total_absent,
            "total_interview":total_interview,
        })

    if download == 'excel':
        return generate_excel(attendance_list, all_dates, search, selected_month, status_type)

    available_months = AttendanceRecord.objects.dates('date', 'month')

    context = {
        "attendance_list": attendance_list,
        "all_dates": all_dates,
        "available_months": available_months,
        "selected_month": selected_month,
        "search": search,
        "status_type": status_type,
    }
    return render(request, "sheet.html", context)

# edit -----------------------------------------------------------


def edit_attendance(request):
    days = range(1, 32)
    months = range(1, 13)
    current_date = datetime.today()
    current_day = current_date.day
    current_month = current_date.month
    current_year = current_date.year

    status_choices = Student.STATUS_CHOICES
    students = Student.objects.all()

    query = request.GET.get("search", "").strip()
    if query:
        students = students.filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query)
        )

    try:
        selected_day = int(request.GET.get("day", current_day))
        selected_month = int(request.GET.get("month", current_month))
        selected_year = int(request.GET.get("year", current_year))
        attendance_date = datetime(selected_year, selected_month, selected_day)
    except ValueError:
        messages.error(request, "Invalid date selection.")
        return redirect("edit_attendance")

    attendance_records = {
        record.student.id: record.status
        for record in AttendanceRecord.objects.filter(date=attendance_date)
    }

    for student in students:
        if student.id not in attendance_records:
            attendance_records[student.id] = "Absent"

    if request.method == "POST":
        for student in students:
            status_key = f"status_{student.id}"
            status_value = request.POST.get(status_key, "Absent")

            AttendanceRecord.objects.update_or_create(
                student=student,
                date=attendance_date,
                defaults={"status": status_value}
            )

            if attendance_date.date() == current_date.date():
                student.status = status_value
                student.save()

        messages.success(request, "Attendance saved successfully!")

        return redirect(f"/edit_attendance?day={selected_day}&month={selected_month}&year={selected_year}&search={query}")


    return render(request, "edit_attendance.html", {
        "days": days,
        "months": months,
        "years": [current_year],
        "students": students,
        "status_choices": status_choices,
        "current_day": current_day,
        "current_month": current_month,
        "current_year": current_year,
        "selected_day": selected_day,
        "selected_month": selected_month,
        "selected_year": selected_year,
        "attendance_records": attendance_records,
        "search_query": query
    })
