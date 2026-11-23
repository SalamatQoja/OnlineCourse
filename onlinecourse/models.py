from decimal import Decimal
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import PositiveIntegerField, PositiveSmallIntegerField
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


class Enrollment(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Актив'
        COMPLETED = 'completed', 'Выполнено'
        CANCELLED = 'cancelled', 'Отменено'

    class Source(models.TextChoices):
        PURCHASE = 'purchase', 'Покупка'
        PROMO = 'promo', 'Промокод'
        FREE = 'free', 'Бесплатно'

    student = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='enrollments', verbose_name='Студент'
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE,
        related_name='enrollments', verbose_name='Курс'
    )
    created = models.DateTimeField(auto_now_add=True, verbose_name='Дата записи')
    status = models.CharField(
        max_length=24, choices=Status.choices,
        default=Status.ACTIVE, verbose_name='Статус'
    )
    source = models.CharField(
        max_length=20, choices=Source.choices,
        default=Source.PURCHASE, verbose_name='Источник'
    )

    class Meta:
        ordering = ['-created']
        verbose_name = 'Запись на курс'
        verbose_name_plural = 'Записи на курсы'
        unique_together = ('student', 'course')  # одна запись на пару

    def __str__(self):
        return f"{self.student.username} → {self.course.course_name}"


class LessonProgress(models.Model):
    class Status(models.TextChoices):
        NOT_STARTED = 'not_started', 'Не начат'
        IN_PROGRESS = 'in_progress', 'В процессе'
        COMPLETED = 'completed', 'Завершён'

    student = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='lesson_progress', verbose_name='Студент'
    )
    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE,
        related_name='lesson_progress', verbose_name='урок'
    )
    status = models.CharField(
        max_length=24, choices=Status.choices,
        default=Status.NOT_STARTED, verbose_name='Статус'
    )
    started_at = models.DateTimeField(
        null=True, blank=True, verbose_name='Начало просмотра'
    )
    completed_at = models.DateTimeField(
        null=True, blank=True, verbose_name='Дата завершения'
    )

    position_seconds = models.PositiveIntegerField(
        default=0, verbose_name='Последняя позиция (сек)'
    )
    watched_seconds = models.PositiveIntegerField(
        default=0, verbose_name='Всего просмотрено (сек)'
    )
    created = models.DateTimeField(auto_now_add=True, verbose_name='Создано')

    class Meta:
        ordering = ['-created']
        unique_together = ('student', 'lesson')  # одна запись на пару
        verbose_name = 'Прогресс урока'
        verbose_name_plural = 'Прогрессы уроков'

    def __str__(self):
        return f"{self.student.username} {self.lesson.name}"

    def is_completed(self):
        return self.status == self.Status.COMPLETED

    @property
    def watched_minutes(self):
        return self.watched_seconds // 60

    @property
    def duration_seconds(self):
        return self.lesson.duration * 60

    @property
    def progress_percent(self):
        if not self.duration_seconds:
            return 0
        return min(100, int(self.position_seconds / self.duration_seconds * 100))

    @property
    def watched_hms(self):
        s = self.watched_seconds or 0
        h, m, sec = s // 3600, (s % 3600) // 60, s % 60
        if h:
            return f"{h} ч {m:02d} мин"
        if m:
            return f"{m} мин {sec:02d} сек"
        return f"{sec} сек"

    @property
    def position_hms(self):
        return self.watched_hms  # тот же формат, но для position

    @property
    def watch_percent(self):
        if not self.duration_seconds:
            return 0
        return min(100, int(self.watched_seconds / self.duration_seconds * 100))


TIME_GRACE_SECONDS = 15


class Quiz(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name='quiz', verbose_name='Урок')
    description = models.TextField(blank=True, verbose_name='Описание')
    pass_score = models.PositiveSmallIntegerField(default=70, validators=[MaxValueValidator(100)],
                                                  verbose_name='Проходной балл (%)')
    max_attempts = models.PositiveSmallIntegerField(default=0, verbose_name='Максимум попыток (0 = без ограничений)')
    time_limit_minutes = PositiveSmallIntegerField(default=0, verbose_name='Лимит времени (мин, 0 = без ограничений)')

    class Meta:
        verbose_name = 'Квиз'
        verbose_name_plural = 'Квизы'

    def __str__(self):
        return f"Квиз: {self.lesson.name}"

    @property
    def total_points(self):
        # sum по .all() использует prefetch_related('questions'), если он был сделан
        return sum(q.points for q in self.questions.all())


class Question(models.Model):
    class Type(models.TextChoices):
        SINGLE = 'single', 'Один правильный'
        MULTIPLE = 'multiple', 'Несколько правильных'
        TEXT = 'text', 'Текстовый ответ'

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions', verbose_name='Квиз')
    text = models.TextField(verbose_name='Текст вопроса')
    type = models.CharField(max_length=15, choices=Type.choices, default=Type.SINGLE, verbose_name='Тип')
    points = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)], verbose_name='Баллы')
    order = models.PositiveSmallIntegerField(default=0, verbose_name='Порядок')
    explanation = models.TextField(blank=True, verbose_name='Пояснение')

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.text[:60]


class AnswerOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options', verbose_name='Вопрос')
    text = models.CharField(blank=False, max_length=255, verbose_name='Текст варианта')
    is_correct = models.BooleanField(default=False, verbose_name='Правильный')
    order = models.PositiveSmallIntegerField(default=0, verbose_name='Порядок')

    class Meta:
        ordering = ['order']
        verbose_name = 'Вариант ответа'
        verbose_name_plural = 'Варианты ответов'

    def __str__(self):
        return self.text

# class QuizAttempt(models.Model):
