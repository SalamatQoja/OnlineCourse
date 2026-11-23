from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Lesson, Quiz


@receiver(post_save, sender=Lesson)
def ensure_quiz_for_quiz_lesson(sender, instance, **kwargs):

    if instance.type == Lesson.Type.QUIZ:
        Quiz.objects.get_or_create(
            lesson=instance,
            defaults={
                'pass_score': 70,
                'max_attempts': 0,
                'time_limit_minutes': 0,
            },
        )
