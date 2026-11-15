from django.contrib.auth import get_user_model
from django.db.models import Count, Q

from onlinecourse.models import Category, Course


def get_role(user):

    if not user.is_authenticated:
        return 'student'

    User = get_user_model()
    role = getattr(user, 'role', None)

    if user.is_superuser or role == User.Roles.ADMIN:
        return 'admin'
    if role == User.Roles.TEACHER:
        return 'teacher'
    return 'student'


def sidebar_context(request):

    published = Q(courses__status=Course.Status.PUBLISHED)
    User = get_user_model()

    return {
        'user_role': get_role(request.user),

        'sidebar_categories': (
            Category.objects
            .annotate(courses_count=Count('courses', filter=published, distinct=True))
            .order_by('name')
        ),

        'sidebar_authors': (
            User.objects
            .annotate(course_count=Count('courses', filter=published, distinct=True))
            .filter(course_count__gt=0)
            .order_by('first_name', 'last_name')
        ),

        'sidebar_courses': (
            Course.objects
            .filter(status=Course.Status.PUBLISHED)
            .order_by('course_name')
        ),
    }