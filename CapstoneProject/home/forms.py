from django import forms
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User
from .models import Interaction

class EditProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Interaction
        fields = ['rating', 'review']
        widgets = {
            "rating": forms.NumberInput(attrs={"min": 1, "max": 5}),
            "review": forms.Textarea(attrs={"rows": 3}),
        }