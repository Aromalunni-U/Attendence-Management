import json
import base64 
from django.db.models import Q
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth import logout
from django.contrib.auth.models import User
from home.models import Stack,Student,Faculty
from django.core.files.base import ContentFile
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect,get_object_or_404



@login_required(login_url='login/')
def admin_dashboard(request):
    search_query = request.GET.get('search', '') 
    stacks = Stack.objects.all()
    stack_id = request.GET.get('stack')
    status = request.GET.get('status')  

    all_students = Student.objects.all()
    if stack_id:
        all_students = all_students.filter(stack_id=stack_id)

    total_students = all_students.count()
    present_students = all_students.filter(status="Present").count()
    absent_students = all_students.filter(status="Absent").count()

    students = all_students  

    if search_query:
        students = students.filter(
            Q(first_name__icontains=search_query) | 
            Q(last_name__icontains=search_query)
        )

    if status:
        students = students.filter(status=status)

    return render(request, 'admin_index.html', {
        "stacks": stacks,
        "students": students,
        "total_students": total_students,  
        "present_students": present_students,
        "absent_students": absent_students,
        "search_query": search_query,
    })

def user_logout(request):
    logout(request)
    return redirect('index')  


# Login _______________________________________________________________________________



def admin_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        user = authenticate(request, username=username, password=password)

        if not user:
            messages.error(request, "Invalid Username or Password!")
            return redirect("login")

        login(request, user)
        messages.success(request, f"Welcome, {user.username}!")
        return redirect('admin_dashboard')

    return render(request, 'login.html')


def add_admin(request):
    users = User.objects.filter(is_staff=True)  

    if request.method == "POST":
        user_id = request.POST.get("user")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        join_date = request.POST.get("join_date")
        image = request.POST.get("image")

        if image: 
            format, imgstr = image.split(';base64,') 
            ext = format.split('/')[-1] 
            image_name = f"{first_name}{last_name}.jpg"
            image = ContentFile(base64.b64decode(imgstr), name=image_name)

        if user_id and first_name and last_name and join_date and image:
            user = User.objects.get(id=user_id)
            Faculty.objects.create(user=user, first_name=first_name, last_name=last_name, join_date=join_date, image=image)
            messages.success(request, "Faculty added successfully!")
            return redirect("add_admin")
        else:
            messages.error(request, "All fields are required!")

    return render(request, "add_admin.html", {"users": users})

# student _________________________________________________________________________

def student_detail(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    
    return render(request, 'student_detail.html', {
        "student": student
    })

def delete_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    student.delete()
    messages.success(request, "Student deleted successfully.")
    return redirect('admin_dashboard')



def edit_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    
    if request.method == "POST":
        student.first_name = request.POST.get("first_name")
        student.last_name = request.POST.get("last_name")
        student.gender = request.POST.get("gender")
        student.phone = request.POST.get("phone")
        student.status = request.POST.get("status")
        student.join_date = request.POST.get("join_date")
        student.info = request.POST.get("info")

        stack_name = request.POST.get("stack")
        stack, created = Stack.objects.get_or_create(stack_name=stack_name)
        student.stack = stack

        if "image" in request.FILES:
            student.image = request.FILES["image"]

        image = request.POST.get("captured_image")
        if image:
            format, imgstr = image.split(";base64,") 
            ext = format.split("/")[-1]  
            image_name = f"{student.first_name}{student.last_name}.jpg"
            image = ContentFile(base64.b64decode(imgstr), name=image_name)
            student.image = image  

        student.save()
        return redirect("student_detail", student_id=student.id)

    return render(request, "edit_student.html", {"student": student})


# Add stack________________________________________________________________________________

def add_stack(request):
    if request.method == "POST":
        stack_name = request.POST.get("stack_name")
        description = request.POST.get("description")

        if stack_name:
            Stack.objects.create(stack_name=stack_name, description=description)
            messages.success(request, "Stack added successfully!")
            return redirect("add_stack")  
        else:
            messages.error(request, "Stack name is required!")
    
    return render(request, "add_stack.html")


# Faculty______________________________________________________________________________

def faculty_list(request):
    if request.method == "POST":
        faculty_id = request.POST.get("faculty_id")
        faculty = get_object_or_404(Faculty, id=faculty_id)
        if faculty.user:
            faculty.user.delete()
        messages.success(request,"Faculty removed successfully")
        return redirect("faculty_list")  

    faculty_members = Faculty.objects.all() 
    return render(request, "view_faculty.html", {"faculty_members": faculty_members})


def create_user(request):
    if request.method == "POST":
        data = json.loads(request.body)
        username = data.get("username")
        password = data.get("password")
        email = data.get("email")

        if not username or not password:
            return JsonResponse({"success": False, "message": "Username and password are required!"})

        if User.objects.filter(username=username).exists():
            return JsonResponse({"success": False, "message": "Username already exists!"})

        user = User.objects.create_user(username=username, password=password, email=email, is_staff=True)
        
        return JsonResponse({"success": True, "message": "User created successfully!", "user_id": user.id})

    return JsonResponse({"success": False, "message": "Invalid request!"})



# stack view__________________________________________________________


def view_stack(request):
    stacks = Stack.objects.all()
    return render(request,"view_stack.html",{"stacks":stacks})


def stack_delete(request, stack_id):
    stack = get_object_or_404(Stack, pk=stack_id)
    stack_name = stack.stack_name
    stack.delete()
    messages.success(request, f'Stack "{stack_name}" deleted successfully!')
    return redirect('view_stack')