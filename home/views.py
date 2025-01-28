from django.shortcuts import render,redirect
from .models import *
from django.contrib import messages
import base64 
from django.core.files.base import ContentFile



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