from django import forms
from .models import Course, Category, Module, Lesson, LessonContent, Quiz, Question


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = (
            'name', 'slug', 'image', 'description',
        )
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input-category-name'}),
            'slug': forms.TextInput(attrs={'class': 'form-input-category-slug'}),
            'description': forms.Textarea(attrs={'class': 'form-input-category-description'}),
        }
        labels = {
            'name': 'имя',
            'slug': 'URL-идентификатор',
            'image': 'изображение',
            'description': 'Описание',
        }
        error_messages = {
            'slug': {
                'unique': 'Категория с таким URL-идентификатором уже существует',
            },
        }

    def clean_parent(self):
        parent = self.cleaned_data.get('parent')
        if parent and self.instance.pk:
            # нельзя сделать родителем самого себя
            if parent.pk == self.instance.pk:
                raise forms.ValidationError('Категория не может быть родителем самой себе')
            # нельзя сделать родителем своего потомка
            node = parent
            while node is not None:
                if node.pk == self.instance.pk:
                    raise forms.ValidationError('Нельзя выбрать потомка как родителя')
                node = node.parent
        return parent


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = (
            'course_name', 'slug', 'description', 'cover',
            'categories', 'language', 'price',
            'status', 'tags',
        )
        widgets = {
            'course_name': forms.TextInput(attrs={'class': 'form-input-course-name'}),
            'slug': forms.TextInput(attrs={'class': 'form-input-course-slug'}),
            'description': forms.Textarea(attrs={'class': 'form-input-course-description', 'rows': 6}),
            'language': forms.TextInput(attrs={'class': 'form-input-course-language'}),
            'price': forms.NumberInput(attrs={'class': 'form-input-course-price', 'step': '0.01'}),
            'tags': forms.Textarea(attrs={'class': 'form-input-course-tags', 'rows': 2}),
        }
        labels = {
            'course_name': 'Название курса',
            'slug': 'URL-идентификатор',
            'description': 'Описание',
            'cover': 'Обложка',
            'categories': 'Категории',
            'language': 'Язык',
            'price': 'Цена (0 = бесплатно)',
            'status': 'Статус',
            'tags': 'Теги (через запятую)',
        }

    def __init__(self, *args, **kwargs):
        self.author = kwargs.pop('author', None)
        super().__init__(*args, **kwargs)
        for field_name in ('categories',):
            self.fields[field_name].widget.attrs['class'] = 'form-input-course-categories'

    def clean_price(self):
        price = self.cleaned_data['price']
        if price < 0:
            raise forms.ValidationError('Цена не может быть отрицательной')
        return price

    def clean_slug(self):
        slug = self.cleaned_data['slug']
        qs = Course.objects.filter(slug=slug)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Курс с таким slug уже существует')
        return slug


class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ['name', 'order']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input-module-name',
                'placeholder': 'Например: Введение в Python',
            }),
            'order ': forms.NumberInput(attrs={
                'class': 'form-input-module-order',
                'min': 0,
            }),
        }
        labels = {
            'name': 'Имя',
            'order': 'Порядок',
        }


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ('name', 'type', 'order', 'duration', 'is_free_preview')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input-lesson-name'}),
            'type': forms.Select(attrs={'class': 'form-input-lesson-type'}),
            'order': forms.NumberInput(attrs={'class': 'form-input-lesson-order'}),
            'duration': forms.NumberInput(attrs={'class': 'form-input-lesson-duration'}),
            'is_free_preview': forms.CheckboxInput(
                attrs={'class': 'form-input-lesson-free'}
            ),
        }
        labels = {
            'name': 'Имя',
            'type': 'Тип',
            'order': 'Порядок',
            'duration': 'Длительность',
            'is_free_preview': 'Бесплатный предпросмотр',
        }


class LessonContentForm(forms.ModelForm):
    class Meta:
        model = LessonContent
        fields = ['video_url', 'text_body', 'file']
        widgets = {
            'video_url': forms.URLInput(attrs={
                'class': 'form-input-content-video',
                'placeholder': 'https://youtube.com/watch?v=...',
            }),
            'text_body': forms.Textarea(attrs={
                'class': 'form-input-content-text',
                'rows': 12,
                'placeholder': 'Текст урока в markdown',
            }),
            'file': forms.ClearableFileInput(attrs={
                'class': 'form-input-content-file',
            }),
        }
        labels = {
            'video_url': 'Ссылка на видео',
            'text_body': 'Текст урока',
            'file': 'Вложение',
        }


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ('description', 'pass_score', 'max_attempts', 'time_limit_minutes')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'pass_score': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'max_attempts': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'time_limit_minutes': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }
        labels = {
            'description': 'Описание',
            'pass_score': 'Проходной балл (%)',
            'max_attempts': 'Максимум попыток (0 = без ограничений)',
            'time_limit_minutes': 'Лимит времени (мин, 0 = без ограничений)',
        }


class QuestionForm(forms.ModelForm):
    class Meta:

        model = Question
        fields = ('text', 'type', 'points', 'order', 'explanation')
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'class': 'form-control-question'}),
            'type': forms.Select(attrs={'class': 'form-control-question-type'}),
            'points': forms.NumberInput(attrs={'class': 'form-control-question-points', 'min': 1}),
            'order': forms.NumberInput(attrs={'class': 'form-control-question-order', 'min': 0}),
            'explanation': forms.Textarea(attrs={'rows': 2, 'class': 'form-control-question-explanation'}),
        }
        labels = {
            'text': 'Текст вопроса',
            'type': 'Тип',
            'points': 'Баллы',
            'order': 'Порядок',
            'explanation': 'Пояснение',
        }
