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
        return reverse('category_detail', kwargs={'slug': self.slug})

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
