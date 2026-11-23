from django.urls import path
from django.contrib.auth import views as auth_views
from users import views as login_users
from . import views

app_name = 'onlinecourse'

urlpatterns = [
    path('', views.index, name='home'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<slug:slug>/edit/', views.category_update, name='category_update'),
    path('categories/', views.category_list, name='category_list'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('category/<slug:slug>delete/', views.category_delete, name='category_delete'),
    path('teacher/course/<slug:slug>/', views.course_detail, name='course_detail'),
    path('teacher/courses/', views.course_list, name='course_list'),
    path('teacher/courses/create/', views.course_create, name='course_create'),
    path('teacher/courses/<slug:slug>/edit/', views.course_update, name='course_update'),
    path('teacher/courses/<slug:slug>/delete/', views.course_delete, name='course_delete'),
    path('modules/', views.module_list, name='module_list'),
    path('module/<int:pk>/', views.module_detail, name='module_detail'),
    path('module/create/<slug:course_slug>/', views.module_create, name='module_create'),
    path('module/<int:pk>edit/', views.module_update, name='module_update'),
    path('module/<int:pk>delete/', views.module_delete, name='module_delete'),
    path('module/<int:module_pk>/lesson/create/', views.lesson_create, name='lesson_create'),
    path('teacher/lessons/', views.lesson_list, name='lesson_list'),
    path('teacher/lesson/<int:pk>/', views.lesson_detail, name='lesson_detail'),
    path('lesson/<int:pk>/edit/', views.lesson_update, name='lesson_update'),
    path('lesson/<int:pk>/delete/', views.lesson_delete, name='lesson_delete'),
    path('lesson/<int:lesson_pk>/content/edit/', views.lesson_content_edit, name='lesson_content_edit'),
    path('lesson/<int:lesson_pk>/content/delete/', views.lesson_content_delete, name='lesson_content_delete'),
    path('course/<slug:slug>/enroll/', views.enrollment_create, name='enrollment_create'),
    path('my/courses/', views.my_enrollments, name='my_enrollments'), path('course/<slug:slug>/enrollments/',
                                                                           views.course_enrollments,
                                                                           name='course_enrollments'),
    path('enrollment/<int:pk>/', views.enrollment_detail, name='enrollment_detail'),
    path('lesson/<int:pk>/progress/', views.update_progress, name='update_progress'),
    path('lesson/<int:pk>/complete/', views.complete_lesson, name='complete_lesson'),
    path('my/progress/', views.my_progress, name='my_progress'),
    path('course/<slug:slug>/progress/', views.course_progress, name='course_progress'),
    path('lesson/<int:pk>/start_lesson/', views.start_lesson, name='start_lesson'),
    path('quiz/question/create/<int:lesson_pk>/', views.quiz_question, name='quiz_question'),
    path('quiz/lesson/<int:lesson_pk>/', views.quiz_detail, name='quiz_detail'),
    path('quiz/list/', views.quiz_list, name='quiz_list'),
    path('question/<int:question_pk>/delete/',
         views.question_delete, name='question_delete'),
]
