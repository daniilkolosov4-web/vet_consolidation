from django import forms
from .models import Visit, Employee, Pet, Owner

class VisitForm(forms.ModelForm):
    search_chip = forms.CharField(
        max_length=15, required=False,
        label='Номер чипа (для поиска)',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите чип для поиска'})
    )
    search_phone = forms.CharField(
        max_length=20, required=False,
        label='Телефон владельца (для поиска)',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Телефон владельца'})
    )

    class Meta:
        model = Visit
        fields = ['clinic', 'pet', 'employee', 'date', 'diagnosis', 'treatment', 'cost']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = Employee.objects.filter(is_active=True)
        self.fields['pet'].required = False
        self.fields['pet'].label_from_instance = lambda obj: f"{obj.name} (чип: {obj.chip_number or 'нет'}, владелец: {obj.owner.full_name if obj.owner else '?'})"

    def clean(self):
        cleaned_data = super().clean()
        search_chip = cleaned_data.get('search_chip')
        search_phone = cleaned_data.get('search_phone')
        pet = cleaned_data.get('pet')

        if pet:
            return cleaned_data

        # Приоритет у чипа
        if search_chip:
            try:
                pet = Pet.objects.get(chip_number=search_chip)
                cleaned_data['pet'] = pet
                return cleaned_data
            except Pet.DoesNotExist:
                self.add_error('search_chip', f'Питомец с чипом {search_chip} не найден')
                return cleaned_data

        if search_phone:
            owners = Owner.objects.filter(phone=search_phone)
            if not owners.exists():
                self.add_error('search_phone', f'Владелец с телефоном {search_phone} не найден')
                return cleaned_data
            pets = Pet.objects.filter(owner__in=owners)
            if not pets.exists():
                self.add_error('search_phone', 'У этого владельца нет зарегистрированных питомцев')
                return cleaned_data
            if pets.count() == 1:
                cleaned_data['pet'] = pets.first()
                return cleaned_data
            else:
                self.add_error('search_phone', f'Найдено несколько питомцев у владельца с телефоном {search_phone}. Пожалуйста, выберите питомца из списка ниже.')
                # Не подставляем питомца, оставляем выбор вручную
                return cleaned_data

        return cleaned_data

class ChipSearchForm(forms.Form):
    chip_number = forms.CharField(
        max_length=15,
        label='Номер чипа',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите 15-значный номер чипа'})
    )