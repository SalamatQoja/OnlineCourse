import markdown
from django.contrib.auth.decorators import login_required
from django.core.mail import message
from django.db.models import Model, Count, Q
from django.http import HttpResponseNotFound, Http404
from django.shortcuts import render, get_object_or_404
from pyexpat import model

from onlinecourse.forms import CourseForm, CategoryForm, ModuleForm, LessonForm, LessonContentForm
from onlinecourse.models import *
from django.db.models import Count, Q, Prefetch
from users.decorators import role_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from users.decorators import role_required
from users.models import User
from .context_processors import get_role
from .models import Course


def index(request):
    return render(request, "onlinecourse/index.html", {"title": "Главная"})


def render_by_role(request, page, context):

    role = get_role(request.user)
    context = {**context, 'role': role}
    return render(request, [
        f'onlinecourse/{role}/{page}.html',
        f'onlinecourse/includes/{page}.html',
    ], context)


@login_required
@role_required(User.Roles.ADMIN.TEACHER)
def category_create(request):
    category_create = Category.objects.filter(author=request.user)

    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Категория «{category.name}» создана')
            return redirect('onlinecourse:category_list')
    else:
        form = CategoryForm()

    return render(request, "onlinecourse/teacher/category_form.html", {
        'form': form,
        'category_create': category_create,
        'title': 'Создание категорий',
        'is_edit': False,
    })


@login_required
@role_required(User.Roles.ADMIN.TEACHER)
def category_update(request, slug):
    category = get_object_or_404(Category, slug=slug, author=request.user)

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f'Категория «{category.name}» обновлена')
            return redirect('onlinecourse:category_list')

    else:
        form = CategoryForm(instance=category)

    return render(request, "onlinecourse/teacher/category_form.html", {
        'form': form,
        'title': f'Редактирование: {category.name}',
        'is_edit': True,
        'category': category,
    })


def category_list(request):
    published = Q(courses__status=Course.Status.PUBLISHED)

    children_qs = Category.objects.annotate(
        cc=Count('courses', filter=published, distinct=True)
    )

    categories = (
        Category.objects
        .filter(parent__isnull=True)
        .prefetch_related(Prefetch('children', queryset=children_qs))
        .annotate(courses_count=Count('courses', filter=published, distinct=True))
    )

    return render_by_role(request, 'category_list', {
        'categories': categories,
        'title': 'Категории курсов',
    })


#
#
# def category_list(request):
#     # children_qs = Category.objects.annotate(cc=Count('courses'))
#     children_qs = Category.objects.annotate(
#         cc=Count('courses', filter=Q(courses__status=Course.Status.PUBLISHED), distinct=True)
#     )
#
#     categories = (
#         Category.objects
#         .filter(parent__isnull=True)
#         .prefetch_related(Prefetch('children', queryset=children_qs))
#         .annotate(courses_count=Count('courses', filter=Q(courses__status=Course.Status.PUBLISHED), distinct=True))
#     )
#     return render(request, "onlinecourse/includes/category_list.html", {
#         "categories": categories,
#         "title": 'Категорий курсов',
#     })

@login_required
def category_detail(request, slug):
    # category = get_object_or_404(Category, slug=slug)
    category = get_object_or_404(
        Category.objects.prefetch_related('children'),
        slug=slug,
    )
    courses = (
        category.courses
        .filter(status=Course.Status.PUBLISHED)
        .order_by('course_name')
    )
    return render_by_role(request, 'category_detail', {
        "category": category,
        "courses": courses,
        # "courses_count": courses_count== bul kerek emes potomushta shablonda
        # {{ category.courses.count }} или {{ courses|length }} bR OTDELNO .count() kerek emes bizde queryset bar ,
        "courses_name": category.name,
    })


@login_required
@role_required(User.Roles.TEACHER)
def category_delete(request, slug):
    category = get_object_or_404(Category, slug=slug, author=request.user)
    if request.method == 'POST':
        category_name = category.name
        category_name.delete()
        messages.success(request, f" Категорий{category_name}: Удален")
        return redirect('onlinecourse:category_list')


@login_required
@role_required(User.Roles.TEACHER)
def course_create(request):
    course = Course.objects.filter(author=request.user)
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.author = request.user
            course.save()
            form.save_m2m()
            messages.success(request, f"Курс{course.course_name} создан")
            return redirect('onlinecourse:course_list')

    else:
        form = CourseForm()

    return render(request, "onlinecourse/teacher/course_form.html", {
        'form': form,
        'course': course,
        'title': 'Создание курса',
        'is_edit': False,
    })


@login_required
def course_detail(request, slug):
    course = get_object_or_404(Course, slug=slug)

    if course.status != Course.Status.PUBLISHED:
        if not request.user.is_authenticated:
            raise Http404
        if request.user != course.author and request.user.role != User.Roles.ADMIN:
            raise Http404

    course = (
        Course.objects
        .prefetch_related('modules', 'categories')
        .select_related('author')
        .get(slug=slug)
    )

    similar_courses = (
        Course.objects
        .filter(categories__in=course.categories.all(),
                status=Course.Status.PUBLISHED
                )
        .exclude(id=course.id)
        .select_related('author')
        .prefetch_related('categories')
        .distinct()
        .order_by('-created')[:5]
    )

    return render_by_role(request, 'course_detail', {
        "course": course,
        "similar_courses": similar_courses,
        "courses_name": course.course_name,
    })


def course_list(request):
    role = get_role(request.user)

    courses = (
        Course.objects
        .select_related('author')
        .prefetch_related('categories')
    )

    if role == 'admin':
        pass  # администратор видит всё
    elif role == 'teacher':
        courses = courses.filter(Q(status=Course.Status.PUBLISHED) | Q(author=request.user))
    else:
        courses = courses.filter(status=Course.Status.PUBLISHED)

    return render_by_role(request, 'course_list', {
        'courses': courses.order_by('-created'),
        'title': 'Все курсы',
    })

#
# def course_list(request):
#     courses = Course.objects.filter(author=request.user).order_by('-created')
#     return render(request, "onlinecourse/teacher/courses_list.html", {
#         "courses": courses,
#         'title': 'Мой курсы',
#     })
# def course_list(request):
#     courses = Course.objects.filter(status=Course.Status.PUBLISHED)
#
#     # учитель видит ещё и свои черновики
#     if request.user.is_authenticated and request.user.role == 'teacher':
#         courses = Course.objects.filter(
#             models.Q(status=Course.Status.PUBLISHED)
#             | models.Q(author=request.user)
#         ).distinct()
#
#     courses = courses.select_related('author').order_by('-created')
#
#     return render(request, "onlinecourse/includes/course_list.html", {
#         'courses': courses,
#     })


@login_required
@role_required(User.Roles.TEACHER)
def course_update(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if course.author != request.user:
        raise PermissionDenied('Вы можете редактировать только свои курсы')

    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            course.save()
            messages.success(request, f'Курс «{course.course_name}» обновлён')
            return redirect('onlinecourse:course_list')
    else:
        form = CourseForm(instance=course)

    return render(request, "onlinecourse/teacher/course_form.html", {
        'form': form,
        'title': f'Редактирование: {course.course_name}',
        'is_edit': True,
        'course': course,
    })


@login_required
@role_required(User.Roles.TEACHER)
def course_delete(request, slug):
    course = get_object_or_404(Course, slug=slug)

    if course.author != request.user:
        raise PermissionDenied('Вы можете удалять только свои курсы')

    if request.method == 'POST':
        name = course.course_name
        course.delete()
        messages.success(request, f"{name} удалён")
        return redirect('onlinecourse:course_list')


@login_required
@role_required(User.Roles.TEACHER)
def module_create(request, course_slug):
    course = get_object_or_404(Course, slug=course_slug, author=request.user)

    if request.method == 'POST':
        form = ModuleForm(request.POST)
        if form.is_valid():
            module = form.save(commit=False)
            module.course = course
            module.save()
            messages.success(request, f"Модуль «{module.name}» добавлен")
            return redirect('onlinecourse:module_list')
    else:
        form = ModuleForm()
    return render(request, "onlinecourse/teacher/module_form.html", {
        'form': form,
        'course': course,
        'title': f"Добавить модуль в{course.course_name}"
    })


@login_required
def module_list(request):
    courses = (
        Course.objects
        .filter(author=request.user)  # ← фильтр по Course, не по Module
        .prefetch_related('modules')
        .order_by('-created')
    )
    return render_by_role(request, 'module_list', {
        'courses': courses,
        'title': 'Модули моих курсов'
    })


@login_required
def module_detail(request, pk):
    module = get_object_or_404(Module.objects.select_related('course__author').prefetch_related('lessons'), pk=pk)
    course = module.course

    is_owner = (request.user == course.author or getattr(request.user, 'role', None) == User.Roles.ADMIN)
    if not is_owner and course.status != Course.Status.PUBLISHED:
        raise Http404

    lessons = module.lessons.all()

    return render_by_role(request, 'module_detail', {
        'module': module,
        'course': course,
        'lessons': lessons,
        'is_owner': is_owner,
        'title': 'Курс модуль'
    })


@login_required
@role_required(User.Roles.TEACHER)
def module_update(request, pk):
    module = get_object_or_404(Module, pk=pk, course__author=request.user)

    if request.method == 'POST':
        form = ModuleForm(request.POST, instance=module)
        if form.is_valid():
            form.save()
            messages.success(request, "Модуль обновлён")
            return redirect('onlinecourse:module_list')
    else:
        form = ModuleForm(instance=module)
    return render(request, "onlinecourse/teacher/module_form.html", {
        'form': form,
        'course': module.course,
        'title': "Редактировать модуль",
    })


@login_required
@role_required(User.Roles.TEACHER)
def module_delete(request, pk):
    module = get_object_or_404(Module, pk=pk, course__author=request.user)

    if request.method == 'POST':
        module.delete()
        messages.success(request, "Модуль удалён")
    return redirect('onlinecourse:module_list')


@login_required
@role_required(User.Roles.TEACHER)
def lesson_create(request, module_pk):
    module = get_object_or_404(Module, pk=module_pk, course__author=request.user)
    if request.method == 'POST':
        form = LessonForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.module = module
            lesson.save()
            messages.success(request, f"Урок «{lesson.name}» добавлен")
            return redirect('onlinecourse:lesson_list')
    else:
        form = LessonForm()
    return render(request, "onlinecourse/teacher/lesson_form.html", {
        'form': form,
        'module': module,
        'course': module.course,
        'title': f"Добавить урок в «{module.name}»",
    })


#
# @login_required
# @role_required(User.Roles.TEACHER)
# def lesson_list(request, module_pk):
#     modules = get_object_or_404(Module, pk=module_pk, course__author=request.user)
#     lessons = modules.lessons.all()
#     return render(request, "onlinecourse/lesson/lesson_list.html", {
#         'module': modules,
#         'course': modules.course,
#         'lessons': lessons,
#         'title': f"Уроки модуля «{modules.name}»",
#     })


@login_required
def lesson_list(request):
    courses = Course.objects.filter(author=request.user)
    all_courses = courses.only('id', 'course_name')
    course_id = request.GET.get('course')
    if course_id and course_id.isdigit():
        courses = courses.filter(id=course_id)

    courses = courses.prefetch_related('modules__lessons').order_by('-created')

    return render_by_role(request, 'lesson_list', {
        'courses': courses,
        'all_courses': all_courses,
        'selected_course': course_id or '',
        'title': 'Уроки моих курсов',
    })


@login_required
@role_required(User.Roles.TEACHER)
def lesson_update(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk, module__course__author=request.user)
    if request.method == 'POST':
        form = LessonForm(request.POST, instance=lesson)
        if form.is_valid():
            form.save()
            messages.success(request, f"Урок обновлен")
            return redirect('onlinecourse:lesson_detail', slug=lesson.module.course.slug)

    else:
        form = LessonForm(instance=lesson)
        return render(request, "onlinecourse/teacher/lesson_form.html", {
            'form': form,
            'module': lesson,
            'title': "Редактировать урок",
        })


@login_required
def lesson_detail(request, pk):
    lesson = get_object_or_404(Lesson.objects.select_related('module__course__author'), pk=pk, )
    course = lesson.module.course

    is_owner = (request.user == course.author or getattr(request.user, 'role', None) == User.Roles.ADMIN)
    if not is_owner and course.status != Course.Status.PUBLISHED:
        raise Http404

    content = getattr(lesson, 'content', None)
    if content and content.text_body:
        content.text_html = markdown.markdown(
            content.text_body,
            extensions=['fenced_code', 'tables']
        )

    return render_by_role(request, 'lesson_detail', {
        'lesson': lesson,
        'course': course,
        'module': lesson.module,
        'content': content,
        'is_owner': is_owner,
        'prev_lesson': lesson.get_prev_lesson(),
        'next_lesson': lesson.get_next_lesson(),
    })


@login_required
@role_required(User.Roles.TEACHER)
def lesson_delete(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk, module__course__author=request.user)
    course_slug = lesson.module.course.slug
    if request.method == 'POST':
        lesson.delete()
        messages.success(request, 'Урок удален')
    return redirect('onlinecourse:lesson_list')


@login_required
@role_required(User.Roles.TEACHER)
def lesson_content_edit(request, lesson_pk):
    lesson = get_object_or_404(Lesson, pk=lesson_pk, module__course__author=request.user)

    try:
        content = lesson.content
    except LessonContent.DoesNotExist:
        content = None

    if request.method == 'POST':
        form = LessonContentForm(
            request.POST,
            request.FILES,
            instance=content,
        )
        if form.is_valid():
            object = form.save(commit=False)
            if content is None:
                object.lesson = lesson
            object.save()
            messages.success(
                request,
                "Контент сохранён" if content else "Контент добавлен"
            )
            return redirect('onlinecourse:lesson_detail', pk=lesson.pk)
    else:
        form = LessonContentForm(instance=content)

    return render(request, "onlinecourse/teacher/content_form.html", {
        'form': form,
        'lesson': lesson,
        'module': lesson.module,
        'course': lesson.module.course,
        'title': (
            "Редактировать контент" if content
            else "Добавить контент"
        ),
    })


@login_required
@role_required(User.Roles.TEACHER)
def lesson_content_delete(request, lesson_pk):
    lesson = get_object_or_404(
        Lesson, pk=lesson_pk,
        module__course__author=request.user
    )
    content = get_object_or_404(LessonContent, lesson=lesson)

    if request.method == 'POST':
        content.delete()
        messages.success(request, "Контент удалён")
        return redirect('onlinecourse:lesson_detail', pk=lesson.pk)

#
# @login_required
# @role_required(User.Roles.TEACHER, User.Roles.ADMIN, User.Roles.STUDENT)
# def enrollment_detail(request, pk):


def page_not_found(request, exception):
    return HttpResponseNotFound("<h1>Страница не найдено</h1>")
