from django import forms
from .models import Visit

class VisitForm(forms.ModelForm):
    class Meta:
        model = Visit
        fields = ['clinic', 'pet', 'employee', 'date', 'diagnosis', 'treatment', 'cost']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

class ChipSearchForm(forms.Form):
    chip_number = forms.CharField(
        max_length=15,
        label='Номер чипа',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите 15-значный номер чипа'})
    )