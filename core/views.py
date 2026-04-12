from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from .models import Visit, Clinic, Pet
from .forms import VisitForm, ChipSearchForm
import csv
import io

def index(request):
    # Получаем параметр фильтра по клинике
    clinic_id = request.GET.get('clinic')
    visits = Visit.objects.all().select_related('clinic', 'pet')
    if clinic_id:
        visits = visits.filter(clinic_id=clinic_id)
    clinics = Clinic.objects.all()

    # Обработка поиска по чипу (форма отправлена методом GET)
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
        'search_form': search_form,
    })

def add_visit(request):
    if request.method == 'POST':
        form = VisitForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Визит успешно добавлен')
            return redirect('index')
    else:
        form = VisitForm()
    return render(request, 'core/add_visit.html', {'form': form})

def pet_detail(request, pk):
    pet = get_object_or_404(Pet, pk=pk)
    visits = pet.visits.all().select_related('clinic').order_by('-date')
    return render(request, 'core/pet_detail.html', {'pet': pet, 'visits': visits})

@staff_member_required
def import_data(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        import_type = request.POST.get('import_type')

        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'Файл должен быть в формате CSV')
            return redirect('import_data')

        # Пытаемся декодировать файл, поддерживая разные кодировки
        try:
            data = csv_file.read().decode('utf-8')
        except UnicodeDecodeError:
            try:
                data = csv_file.read().decode('cp1251')
            except UnicodeDecodeError:
                messages.error(request, 'Не удалось распознать кодировку файла. Используйте UTF-8 или Windows-1251')
                return redirect('import_data')

        io_string = io.StringIO(data)
        reader = csv.DictReader(io_string)

        if import_type == 'pets':
            # Импорт питомцев
            created_count = 0
            skipped_count = 0
            for row in reader:
                chip = row.get('chip_number', '').strip()
                if not chip:
                    continue

                clinic_name = row.get('clinic_name', '').strip()
                clinic, _ = Clinic.objects.get_or_create(name=clinic_name)

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
                if created:
                    created_count += 1
                else:
                    skipped_count += 1
            messages.success(request, f'Импорт питомцев завершён. Создано: {created_count}, пропущено (уже есть): {skipped_count}')

        elif import_type == 'visits':
            # Импорт визитов
            created_count = 0
            errors = []
            for row in reader:
                chip = row.get('chip_number', '').strip()
                if not chip:
                    continue

                try:
                    pet = Pet.objects.get(chip_number=chip)
                except Pet.DoesNotExist:
                    errors.append(f'Питомец с чипом {chip} не найден')
                    continue

                clinic_name = row.get('clinic_name', '').strip()
                try:
                    clinic = Clinic.objects.get(name=clinic_name)
                except Clinic.DoesNotExist:
                    errors.append(f'Клиника "{clinic_name}" не найдена')
                    continue

                Visit.objects.create(
                    pet=pet,
                    clinic=clinic,
                    date=row.get('date'),
                    diagnosis=row.get('diagnosis', ''),
                    treatment=row.get('treatment', ''),
                    cost=row.get('cost', 0)
                )
                created_count += 1
            messages.success(request, f'Импорт визитов завершён. Добавлено: {created_count}.')
            if errors:
                messages.warning(request, f'Ошибки: {", ".join(errors[:5])}')

        return redirect('import_data')

    return render(request, 'core/import.html')