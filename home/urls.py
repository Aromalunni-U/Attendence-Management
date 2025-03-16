from django.urls import path
from .views import *

urlpatterns = [
    path('',index,name='index'),
    path("sheet",sheet,name="sheet"),
    path("add_student/",add_student,name="add_student"),
    path('video_stream/', video_stream, name='video_stream'),
    path('attendance/', attendance, name='attendance'),
    path("faculty_login",faculty_login,name="faculty_login"),
    path('edit_attendance', edit_attendance, name='edit_attendance'),

]
