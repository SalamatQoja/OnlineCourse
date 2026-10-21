from django.contrib.auth.views import LogoutView, PasswordChangeView, PasswordChangeDoneView, PasswordResetView, \
    PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.urls import path

from . import views
from .views import user_list, change_user_role

app_name = 'users'

urlpatterns = [
    path('login/', views.LoginUser.as_view(), name='login'),
    path('register/', views.RegisterUser.as_view(), name='register'),
    path('register/email/', views.register_email, name='register_email'),
    path('register/verify/', views.verify_code, name='verify_code'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('redirect/', views.post_login_redirect, name='post_login_redirect'),
    path('profile/', views.ProfilUser.as_view(), name='profile'),
    path('password-change/', views.UserPasswordChange.as_view(), name='password_change'),
    path('password-change/done/', PasswordChangeDoneView.as_view(template_name='users/password_change_done.html'),
         name='password_change_done'),
    path('dashboard/users/', user_list, name='user_list'),
    path('dashboard/users/<int:user_id>/role/', change_user_role, name='change_user_role'),
    path('users/<int:user_id>/change-password/', views.change_user_password, name='change_user_password'),
    path('admin-panel/', views.admin_sidebar, name='admin_sidebar'),
    path('teacher/', views.teacher_sidebar, name='teacher_sidebar'),
    path('student/', views.student_sidebar, name='student_sidebar'),
    path('users/<int:user_id>/block/', views.block_user, name='block_user'),
    path('users/<int:user_id>/unblock/', views.unblock_user, name='unblock_user'),
]
