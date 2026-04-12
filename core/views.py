from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from .models import Pet, Visit, Clinic
from .forms import ChipSearchForm, VisitForm
import csv
import io

def index(request):
    clinic_id = request.GET.get('clinic')
    visits = Visit.objects.all().select_related('clinic', 'pet')
    if clinic_id:
        visits = visits.filter(clinic_id=clinic_id)
    clinics = Clinic.objects.all()
    
    # Форма поиска по чипу
    search_form = ChipSearchForm(request.GET or None)
    if search_form.is_valid() and search_form.cleaned_data.get('chip_number'):
        chip = search_form.cleaned_data['chip_number']
        try:
            pet = Pet.objects.get(chip_number=chip)
            return redirect('pet_detail', pk=pet.pk)
        except Pet.DoesNotExist:
            messages.error(request, f'Питомец с чипом {chip} не найден')
    
    return render(request, 'core/index.html', {
        'visits': visits, 
        'clinics': clinics,
        'search_form': search_form
    })

def pet_detail(request, pk):
    pet = get_object_or_404(Pet, pk=pk)
    visits = pet.visits.all().select_related('clinic').order_by('-date')
    return render(request, 'core/pet_detail.html', {'pet': pet, 'visits': visits})

@staff_member_required
def import_data(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        # Определяем тип импорта (питомцы или визиты)
        import_type = request.POST.get('import_type')
        
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'Файл должен быть в формате CSV')
            return redirect('import_data')
        
        data = csv_file.read().decode('utf-8')
        io_string = io.StringIO(data)
        reader = csv.DictReader(io_string)
        
        if import_type == 'pets':
            # Импорт питомцев
            for row in reader:
                chip = row.get('chip_number', '').strip()
                if not chip:
                    continue  # пропускаем без чипа
                
                # Ищем клинику по названию
                clinic_name = row.get('clinic_name', '').strip()
                clinic, _ = Clinic.objects.get_or_create(name=clinic_name)
                
                # Ищем питомца по чипу
                pet, created = Pet.objects.get_or_create(
                    chip_number=chip,
                    defaults={
                        'name': row.get('name', ''),
                        'animal_type': row.get('animal_type', ''),
                        'age': row.get('age') or None,
                        'owner_name': row.get('owner_name', ''),
                        'clinic': clinic,
                    }
                )
                if not created:
                    messages.warning(request, f'Питомец с чипом {chip} уже существует, пропущен')
            messages.success(request, 'Импорт питомцев завершён')
        
        elif import_type == 'visits':
            # Импорт визитов
            for row in reader:
                chip = row.get('chip_number', '').strip()
                if not chip:
                    continue
                try:
                    pet = Pet.objects.get(chip_number=chip)
                except Pet.DoesNotExist:
                    messages.error(request, f'Питомец с чипом {chip} не найден, визит пропущен')
                    continue
                
                clinic_name = row.get('clinic_name', '').strip()
                try:
                    clinic = Clinic.objects.get(name=clinic_name)
                except Clinic.DoesNotExist:
                    messages.error(request, f'Клиника "{clinic_name}" не найдена, визит пропущен')
                    continue
                
                Visit.objects.create(
                    pet=pet,
                    clinic=clinic,
                    date=row.get('date'),
                    diagnosis=row.get('diagnosis', ''),
                    treatment=row.get('treatment', ''),
                    cost=row.get('cost', 0)
                )
            messages.success(request, 'Импорт визитов завершён')
        
        return redirect('import_data')
    
    return render(request, 'core/import.html')