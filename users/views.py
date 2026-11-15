import random

from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.core.mail import send_mail
from django.conf import settings
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView

from onlinecourse.models import Category, Course
from .decorators import role_required
from .mixins import RoleTemplateMixin
from .models import EmailVerification, User
from .forms import EmailVerificationForm, CodeVerificationForm, ProfileUserForm, LoginFormUsers, RegisterFormUsers, \
    PasswordChangeForm, AdminSetPasswordForm


class LoginUser(LoginView):
    form_class = LoginFormUsers
    template_name = 'users/login.html'
    extra_context = {'title': 'Вход'}
    success_url = reverse_lazy('home')

    def get_success_url(self):
        return reverse_lazy('users:post_login_redirect')


class ProfilUser(LoginRequiredMixin, RoleTemplateMixin, UpdateView):
    model = get_user_model()
    form_class = ProfileUserForm
    page = 'profile'  # -> onlinecourse/<роль>/profile.html
    fallback_template = 'users/profile.html'  # запасной, пока файлы ролей не созданы
    # template_name = 'users/profile.html'
    extra_context = {'title': 'Профиль пользовителя',
                     'default_image': settings.DEFAULT_USER_IMAGE}

    def get_success_url(self):
        return reverse_lazy('users:profile')

    def get_object(self, queryset=None):
        return self.request.user


def register_email(request):
    if request.method == 'POST':
        form = EmailVerificationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            code = f"{random.randint(0, 999999):06d}"
            EmailVerification.objects.create(email=email, code=code)

            send_mail(
                subject='Код подтверждения',
                message=f'Ваш код: {code}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            request.session['verify_email'] = email
            messages.success(request, 'Код отправлен на почту')
            return redirect('users:verify_code')
    else:
        form = EmailVerificationForm()
    return render(request, 'users/register_email.html', {'form': form})


def verify_code(request):
    email = request.session.get('verify_email')
    if not email:
        return redirect('users:register_email')

    if request.method == 'POST':
        form = CodeVerificationForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            record = EmailVerification.objects.filter(
                email=email, code=code, is_used=False
            ).last()
            if not record or record.is_expired():
                messages.error(request, 'Код неверный или истёк')
            else:
                record.is_used = True
                record.save()
                request.session['email_verified'] = True
                return redirect('users:register')
    else:
        form = CodeVerificationForm()
    return render(request, 'users/verify_code.html', {'form': form})


class RegisterUser(CreateView):
    form_class = RegisterFormUsers
    template_name = 'users/register.html'
    extra_context = {'title': 'Регистрация'}
    success_url = reverse_lazy('onlinecourse:home')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(
            self.request,
            self.object,
            backend='django.contrib.auth.backends.ModelBackend',
        )
        return response


class UserPasswordChange(RoleTemplateMixin, PasswordChangeView):
    form_class = PasswordChangeForm
    page = 'password_change_form'
    fallback_template = 'users/password_change_form.html'
    success_url = reverse_lazy('users:password_change_done')
    extra_context = {'title': 'Смена пароля'}


@login_required
def post_login_redirect(request):
    role = getattr(request.user, 'role', None)

    if role == User.Roles.ADMIN:
        return redirect('users:admin_dashboard')
    if role == User.Roles.STUDENT:
        return redirect('users:student_dashboard')
    if role == User.Roles.TEACHER:
        return redirect('users:teacher_dashboard')

    messages.error(request, "Неизвестная роль пользователя")
    return redirect('onlinecourse:home')


# @login_required
# def post_login_redirect(request):
#     role = request.user.role
#
#     if role == User.Roles.ADMIN:
#         return redirect('users:admin_dashboard')  # или 'admin:index'
#     elif role == User.Roles.STUDENT:
#         return redirect('users:student_dashboard')  # ученик → каталог
#     elif role == User.Roles.TEACHER:
#         return redirect('users:teacher_dashboard')  # учитель → мои курсы
#     else:
#         return redirect('users:login')
# if role == User.Roles.ADMIN:
#     return redirect('users:admin_sidebar')
# elif role == User.Roles.STUDENT:
#     return redirect('users:student_sidebar')
# elif role == User.Roles.TEACHER:
#     return redirect('users:teacher_sidebar')
# else:
#     return redirect('users:login')


@login_required
@role_required(User.Roles.ADMIN)
def user_list(request):
    users = User.objects.all().order_by('date_joined')
    paginator = Paginator(users, 10)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)
    return render(request, 'users/user_list.html', {
        'page_object': page_object,
        'roles': User.Roles.choices,
    })


@login_required
def author_list(request):
    authors = (
        User.objects
        .filter(role=User.Roles.TEACHER)
        .order_by('last_name', 'first_name')
    )
    paginator = Paginator(authors, 10)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)
    return render(request, 'users/author_list.html', {
        'page_object': page_object,
    })


@login_required
def author_detail(request, pk):
    author = get_object_or_404(User, pk=pk, role=User.Roles.TEACHER)
    courses = author.courses.filter(status=Course.Status.PUBLISHED)
    return render(request, 'users/author_detail.html', {
        'author': author,
        'courses': courses,
    })


@login_required
@role_required(User.Roles.ADMIN)
def change_user_role(request, user_id):
    if request.method != 'POST':
        return redirect('users:user_list')

    target_user = get_object_or_404(User, id=user_id)
    new_role = request.POST.get('role')

    # валидация: роль должна быть из допустимых choices
    valid_roles = {r.value for r in User.Roles}
    if new_role not in valid_roles:
        messages.error(request, 'Некорректная роль')
        return redirect('users:user_list')

    # защита: нельзя менять роль самому себе (иначе можно случайно лишиться прав)
    if target_user == request.user:
        messages.error(request, 'Нельзя менять роль самому себе')
        return redirect('users:user_list')

    target_user.role = new_role
    target_user.save(update_fields=['role'])
    messages.success(request, f'Роль пользователя {target_user.username} изменена на {new_role}')
    return redirect('users:user_list')


@login_required
@role_required(User.Roles.TEACHER, User.Roles.ADMIN)
def teacher_dashboard(request):
    courses = (
        Course.objects.filter(author=request.user)
        .prefetch_related('modules__lessons')
        .order_by('-created')

    )
    return render(request, 'onlinecourse/teacher/layout.html', {  # ← дочерний
        'courses': courses,
    })


@login_required
@role_required(User.Roles.ADMIN)
def admin_dashboard(request):
    return render(request, 'users/admin_dashboard.html', {  # ← дочерний
        'user_count': User.objects.count(),
        'course_count': Course.objects.count(),
    })


@login_required
@role_required(User.Roles.STUDENT)
def student_dashboard(request):
    return render(request, 'onlinecourse/student/layout.html', {})


@login_required
@role_required('admin')
def change_user_password(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)

    if request.method == 'POST':
        form = AdminSetPasswordForm(target_user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'Пароль пользователя {target_user.username} изменён'
            )
            return redirect('users:users_list')
    else:
        form = AdminSetPasswordForm(target_user)

    return render(request, 'users/change_users_password.html', {
        'form': form,
        'target_user': target_user,
    })


@login_required
@role_required('admin')
def block_user(request, user_id):
    target_user_block = get_object_or_404(User, pk=user_id)

    if target_user_block == request.user:
        messages.error(request, 'Нельзя заблокировать самого себя')
        return redirect('users:user_list')

    if target_user_block.is_superuser and not request.user.is_superuser:
        messages.error(request, 'Только суперпользователь может блокировать суперпользователя')
        return redirect('users:user_list')

    if request.method == 'POST':
        target_user_block.is_active = False
        target_user_block.save(update_fields=['is_active'])

        # _kill_user_sessions(target)

        messages.success(request, f'Пользователь {target_user_block.username} заблокирован')
        return redirect('users:user_list')

    if target_user_block.role == User.Roles.ADMIN:
        active_admins = User.objects.filter(role=User.Roles.ADMIN, is_active=True).exclude(pk=target_user_block.pk)
        if not active_admins.exists():
            messages.error(request, 'Нельзя заблокировать последнего активного администратора')
            return redirect('users:user_list')

    return render(request, 'users/user_block_confirm.html', {
        'target_user': target_user_block,
    })


@login_required
@role_required('admin')
def unblock_user(request, user_id):
    target_user_unblock = get_object_or_404(User, pk=user_id)

    if request.method == 'POST':
        target_user_unblock.is_active = True
        target_user_unblock.save(update_fields=['is_active'])
        messages.success(request, f'Пользователь {target_user_unblock.username} разблокирован')
        return redirect('users:user_list')

    return render(request, 'users/user_unblock_confirm.html', {
        'target_user': target_user_unblock,
    })
