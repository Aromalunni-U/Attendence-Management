from django.urls import path
from .views import *

urlpatterns = [
    path('login/', admin_login, name='login'),
    path('dashboard', admin_dashboard, name='admin_dashboard'),
    path('logout', user_logout, name='logout'),
    path("add_admin",add_admin,name="add_admin"),
    path('student/<int:student_id>/', student_detail, name='student_detail'),
    path('student/<int:student_id>/edit/', edit_student, name='edit_student'),
    path("add_stack",add_stack,name="add_stack"),
    path("faculty/", faculty_list, name="faculty_list"), 
    path("create_user/", create_user, name="create_user"),
    path("stack/",view_stack,name="view_stack"),
    path('stacks/<int:stack_id>/delete/', stack_delete, name='stack_delete'),
    path('delete_student/<int:student_id>/', delete_student, name='delete_student'),

]
