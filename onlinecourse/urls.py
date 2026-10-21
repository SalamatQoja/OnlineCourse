from django.urls import path
from django.contrib.auth import views as auth_views
from users import views as login_users
from . import views

app_name = 'onlinecourse'

urlpatterns = [
    path('', views.index, name='home'),
    path('categories/', views.category_list, name='category_list'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('course/<slug:slug>/', views.course_detail, name='course_detail'),
    # path('login/', views.login, name='login'),
]
