from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse

from sitestudy import settings
from users.models import User


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/%Y/%m', null=True, blank=True, verbose_name='Изображение', )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='children',
        verbose_name='Родительская категория',
    )
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('onlinecourse:category_detail', kwargs={'slug': self.slug})

    def get_course_count(self):
        return self.courses.count()

    def clean(self):
        depth = 1
        parent = self.parent
        while parent is not None:
            depth += 1
            if depth > 3:
                raise ValidationError('Максимальная вложенность — 3 уровня')
            parent = parent.parent

    class Meta:
        ordering = ['name']
        verbose_name = 'Категория'
        verbose_name_plural = 'Категорий'


class Course(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Черновик'
        REVIEW = 'review', 'На проверке'
        PUBLISHED = 'published', 'Опубликован'
        ARCHIVED = 'archived', 'В архиве'

    course_name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, db_index=True)
    description = models.TextField()
    cover = models.ImageField(upload_to='courses/%Y/%m')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='courses')
    categories = models.ManyToManyField(Category, verbose_name="Категоры", related_name="courses", blank=True)
    level = models.IntegerField(default=0)
    language = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), blank=True, )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    tags = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.course_name}"

    def get_absolute_url(self):
        return reverse('onlinecourse:course_detail', kwargs={'slug': self.slug})

    def get_tags_list(self):
        return [t.strip() for t in self.tags.split(',') if t.strip()]

    class Meta:
        ordering = ['-created']


class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules', verbose_name='Курс')
    name = models.CharField(max_length=250, verbose_name='Название модуля')
    order = models.IntegerField(default=0, verbose_name='Порядок')

    class Meta:
        ordering = ['order']
        verbose_name = 'Модуль'
        verbose_name_plural = 'Модули'

    def __str__(self):
        return f"{self.course.course_name} — {self.name}"

    def get_absolute_url(self):
        return reverse('onlinecourse:course_detail',
                       kwargs={'slug': self.course.slug})


class Lesson(models.Model):
    class Type(models.TextChoices):
        VIDEO = 'video', 'Видео'
        TEXT = 'text', 'Текст'
        File = 'file', 'Файл'
        QUIZ = 'quiz', 'Вопрос'
        ASSIGNMENT = 'assignment' 'Ответ'

    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons', verbose_name='Модуль')
    name = models.CharField(max_length=250, verbose_name='Название')
    type = models.CharField(max_length=15, choices=Type.choices, default=Type.VIDEO, verbose_name='Тип')
    order = models.IntegerField(default=0, verbose_name='Порядок')
    duration = models.IntegerField(default=0, verbose_name='Длительность (мин)')
    is_free_preview = models.BooleanField(default=False, verbose_name='Бесплатный предпросмотр')

    class Meta:
        ordering = ['order']
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'

    def __str__(self):
        return self.name

    def get_next_lesson(self):
        return (
            Lesson.objects
            .filter(module=self.module, order__gt=self.order)
            .order_by('order')
            .first()
        )

    def get_prev_lesson(self):
        return (
            Lesson.objects
            .filter(module=self.module, order__lt=self.order)
            .order_by('-order')
            .first()
        )


class LessonContent(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name='content', verbose_name='Урок')
    video_url = models.URLField(blank=True, verbose_name='Ссылка на видео')
    text_body = models.TextField(blank=True, verbose_name='Текст урока')
    file = models.FileField(upload_to='lessons/content/%Y/%m', blank=True, null=True, verbose_name='Вложение')

    class Meta:
        verbose_name = 'Контент урока'
        verbose_name_plural = 'Контент уроков'

    def __str__(self):
        return f"Контент: {self.lesson.name}"


class Enrollment():
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Актив'
        COMPLETED = 'completed', 'Выполнено'
        CANCELLED = 'cancelled', 'Отменятся'

    class Source(models.TextChoices):
        PURCHASE = 'purchase', 'Покупка'
        PROMO = 'promo', 'промокод'
        FREE = 'free', 'бесплатно'

    student = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='enrollments',
                                verbose_name='Записыватся')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.ACTIVE)
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.PURCHASE)

    class Meta:
        ordering = ['-date']
        verbose_name = 'Запись на урок'
        verbose_name_plural = 'Запись на уроке'




