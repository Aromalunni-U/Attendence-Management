from django.shortcuts import render,redirect



# index------------------------------------------------

def index(request):
    return render(request,"index.html")

# sheet------------------------------------------------

def sheet(request):
    return render(request,"sheet.html")

# add student------------------------------------------

def add_student(request):
    return render(request,"add_student.html")