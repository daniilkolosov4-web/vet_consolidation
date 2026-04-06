from django import forms
from .models import Visit

class VisitForm(forms.ModelForm):
    class Meta:
        model = Visit
        fields = ['clinic', 'pet', 'date', 'diagnosis', 'treatment', 'cost']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }