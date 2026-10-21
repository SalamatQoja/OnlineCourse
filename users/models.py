from django.contrib.auth.models import AbstractUser
from django.db import models
import random
from django.utils import timezone
from datetime import timedelta


class User(AbstractUser):
    class Roles(models.TextChoices):
        STUDENT = 'student', 'Студент'
        TEACHER = 'teacher', 'Преподаватель'
        ADMIN = 'admin', 'Администратор'

    class Gender(models.TextChoices):
        MALE = 'male', 'Мужской'
        FEMALE = 'female', 'Женский'
        OTHER = 'other', 'Другой'

    role = models.CharField(max_length=10, choices=Roles.choices, default=Roles.STUDENT, verbose_name='Роль')
    photo = models.ImageField(upload_to='users/%Y/%m/%d', null=True, blank=True, verbose_name='Фотография')
    gender = models.CharField(max_length=10, choices=Gender.choices, blank=True, null=True, verbose_name='Пол')
    bio = models.TextField(blank=True, verbose_name='О себе')
    passport = models.CharField(max_length=20,blank=True, verbose_name='Паспорт')
    birth_date = models.DateField(blank=True, null=True, verbose_name='Дата рождения')
    email = models.EmailField(unique=True, verbose_name='E-mail')  # важно для регистрации по email
    phone_number = models.CharField(max_length=50, blank=True, verbose_name='Телефон номер')

    def __str__(self):
        return self.username

    ONLINE_THRESHOLD = timedelta(minutes=15)

    def get_status(self):
        if not self.is_active:
            return 'blocked'
        if self.last_login and self.last_login >= timezone.now() - self.ONLINE_THRESHOLD:
            return 'online'
        return 'offline'

    def is_online(self):
        return self.get_status() == 'online'

    def is_blocked(self):
        return not self.is_active


def generate_code():
    return f"{random.randint(0, 999999):06d}"


class EmailVerification(models.Model):
    email = models.EmailField()
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=15)

    def __str__(self):
        return f"{self.email} — {self.code}"
