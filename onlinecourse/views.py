from django.db.models import Model, Count
from django.http import HttpResponseNotFound
from django.shortcuts import render, get_object_or_404

from onlinecourse.models import *


def index(request):
    return render(request, "onlinecourse/index.html", {"title": "Главная"})


def category_list(request):
    children_qs = Category.objects.annotate(cc=Count('courses'))
    categories = (
        Category.objects
        .filter(parent__isnull=True)
        .prefetch_related(Prefetch('children', queryset=children_qs))
        .annotate(courses_count=Count('courses', distinct=True))
    )
    return render(request, "onlinecourse/category_list.html", {
        "categories": categories,
        "title": 'Категорий курсов',
    })


def category_detail(request, slug):
    # category = get_object_or_404(Category, slug=slug)
    category = get_object_or_404(
        Category.objects.prefetch_related('children'),
        slug=slug,
    )
    courses = category.courses.all().order_by('course_name')
    return render(request, "onlinecourse/category_detail.html", {
        "category": category,
        "courses": courses,
        # "courses_count": courses_count== bul kerek emes potomushta shablonda
        # {{ category.courses.count }} или {{ courses|length }} bR OTDELNO .count() kerek emes bizde queryset bar ,
        "courses_name": category.name,
    })


def course_detail(request, slug):
    course = get_object_or_404(Course, slug=slug)
    similar_courses = (
        Course.objects
        .filter(categories__in=course.categories.all())
        .exclude(id=course.id)
        .select_related('author')
        .prefetch_related('categories')
        .distinct()
        .order_by('-created')[:5]
    )

    return render(request, "onlinecourse/course_detail.html", {
        "course": course,
        "similar_courses": similar_courses,
        "courses_name": course.course_name,
    })


def page_not_found(request, exception):
    return HttpResponseNotFound("<h1>Страница не найдено</h1>")
