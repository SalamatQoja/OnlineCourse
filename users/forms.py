import datetime
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, PasswordChangeForm, SetPasswordForm

User = get_user_model()


class LoginFormUsers(AuthenticationForm):
    username = forms.CharField(
        label='Логин', widget=forms.TextInput(attrs={'class': 'form-input-login'})
    )
    password = forms.CharField(
        label='Пароль', widget=forms.PasswordInput(attrs={'class': 'form-input-password'})
    )


class RegisterFormUsers(UserCreationForm):
    username = forms.CharField(
        label='Логин', widget=forms.TextInput(attrs={'class': 'form-input-register-username'})
    )
    email = forms.EmailField(
        label='E-mail', widget=forms.TextInput(attrs={'class': 'form-input-register-email'})
    )
    password1 = forms.CharField(
        label='Пароль', widget=forms.PasswordInput(attrs={'class': 'form-input-register-password'})
    )
    password2 = forms.CharField(
        label='Повтор пароля', widget=forms.PasswordInput(attrs={'class': 'form-input-register-password'})
    )

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name',
            'password1', 'password2',
            'bio', 'passport', 'phone_number', 'gender',
        )
        labels = {
            'email': 'E-mail',
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'bio': 'О себе',
            'passport': 'Паспорт',
            'phone_number': 'Телефон',
            'gender': 'Пол',
        }
        widgets = {
            'email': forms.TextInput(attrs={'class': 'form-input-register-email'}),
            'first_name': forms.TextInput(attrs={'class': 'form-input-register-firstname'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input-register-lastname'}),
            'bio': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'passport': forms.TextInput(attrs={'class': 'form-input-register-passport'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-input-register-phonenumber'}),
            'gender': forms.Select(attrs={'class': 'form-input-register-gender'}),
        }

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Такой E-mail уже существует!')
        return email


class ProfileUserForm(forms.ModelForm):
    username = forms.CharField(
        disabled=True, label='Логин',
        widget=forms.TextInput(attrs={'class': 'form-input-register-username'})
    )
    email = forms.EmailField(
        disabled=True, label='E-mail',
        widget=forms.TextInput(attrs={'class': 'form-input-register-email'})
    )

    this_year = datetime.date.today().year
    birth_date = forms.DateField(
        label='Дата рождения',
        widget=forms.SelectDateWidget(
            years=tuple(range(this_year - 100, this_year - 5))
        ),
        required=False,
    )

    class Meta:
        model = User
        fields = ('photo', 'username', 'email', 'birth_date',
                  'first_name', 'last_name', 'gender', 'bio',
                  'passport', 'phone_number')
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'gender': 'Пол',
            'bio': 'О себе',
            'passport': 'Паспорт',
            'phone_number': 'Телефон номер'
        }
        widgets = {
            'email': forms.TextInput(attrs={'class': 'form-input-register-email'}),
            'first_name': forms.TextInput(attrs={'class': 'form-input-register-firstname'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input-register-lastname'}),
            'bio': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'passport': forms.TextInput(attrs={'class': 'form-input-register-passport'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-input-register-phonenumber'}),
            'gender': forms.Select(attrs={'class': 'form-input-register-gender'}),
        }


class EmailVerificationForm(forms.Form):
    email = forms.EmailField(
        label='E-mail', widget=forms.EmailInput(attrs={'class': 'form-input-email-registration'})
    )


class CodeVerificationForm(forms.Form):
    code = forms.CharField(
        label='Код из сообщение', max_length=7,
        widget=forms.TextInput(attrs={'class': 'form-input-verificationcode'})
    )


class PasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(label='Старый пароль',
                                   widget=forms.PasswordInput(attrs={'class': 'form-input-change-for-users1'}))
    new_password1 = forms.CharField(label='Новый пароль',
                                    widget=forms.PasswordInput(attrs={'class': 'form-input-change-for-users2'}))
    new_password2 = forms.CharField(label='Потверждение пароль',
                                    widget=forms.PasswordInput(attrs={'class': 'form-input-change-for-users3'}))


class AdminSetPasswordForm(SetPasswordForm):
    class Meta:
        model = User
        fields = ('new_password1', 'new_password2',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].widget = forms.PasswordInput(
            attrs={'class': 'form-input-users-change-password', 'autocomplete': 'new-password'})
        self.fields['new_password2'].widget = forms.PasswordInput(
            attrs={'class': 'form-input-users-change-password', 'autocomplete': 'new-password'}
        )
        self.fields['new_password1'].label = 'Новый пароль'
        self.fields['new_password2'].label = 'Повтор нового пароля'
