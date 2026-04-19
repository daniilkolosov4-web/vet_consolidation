from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from .models import Visit, Clinic, Pet, Owner, Employee
from .forms import VisitForm, ChipSearchForm
import csv
import io

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ НЕЧЁТКОГО СРАВНЕНИЯ ==========

def levenshtein_distance(a, b):
    """Расстояние Левенштейна между двумя строками (регистронезависимо)"""
    if not a or not b:
        return 0
    a, b = a.lower(), b.lower()
    if len(a) < len(b):
        a, b = b, a
    previous_row = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        current_row = [i + 1]
        for j, cb in enumerate(b):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (ca != cb)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

def normalized_similarity(a, b):
    """Нормализованное сходство двух строк (0..1), 1 = полное совпадение"""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    dist = levenshtein_distance(a, b)
    max_len = max(len(a), len(b))
    return 1.0 - (dist / max_len)

# ========== ОСНОВНЫЕ ПРЕДСТАВЛЕНИЯ ==========

def index(request):
    clinic_id = request.GET.get('clinic')
    visits = Visit.objects.all().select_related('clinic', 'pet', 'employee')
    if clinic_id:
        visits = visits.filter(clinic_id=clinic_id)
    clinics = Clinic.objects.all()

    # Поиск по чипу
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
    visits = pet.visits.all().select_related('clinic', 'employee').order_by('-date')
    return render(request, 'core/pet_detail.html', {'pet': pet, 'visits': visits})

@staff_member_required
def import_data(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        import_type = request.POST.get('import_type')

        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'Файл должен быть в формате CSV')
            return redirect('import_data')

        # Декодирование файла (UTF-8 или Windows-1251)
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
            created_count = 0
            skipped_chip = 0
            skipped_fuzzy = 0
            for row in reader:
                chip = row.get('chip_number', '').strip()
                # ---- 1. Если есть чип - точный поиск ----
                if chip:
                    if Pet.objects.filter(chip_number=chip).exists():
                        skipped_chip += 1
                        continue
                    else:
                        _create_pet_from_row(row)
                        created_count += 1
                        continue
                
                # ---- 2. Нет чипа - нечёткое сравнение по нескольким полям ----
                name = row.get('name', '').strip()
                animal_type = row.get('animal_type', '').strip()
                breed = row.get('breed', '').strip()
                color = row.get('color', '').strip()
                owner_full_name = row.get('owner_name', '').strip()

                # Ограничим кандидатов по виду для ускорения (если вид указан)
                candidates = Pet.objects.filter(animal_type=animal_type) if animal_type else Pet.objects.all()
                best_score = 0.0
                best_pet = None
                for candidate in candidates:
                    score = 0.0
                    # кличка (вес 0.25)
                    if name and candidate.name:
                        score += 0.25 * normalized_similarity(name, candidate.name)
                    # вид (вес 0.2) - точное совпадение
                    if animal_type and candidate.animal_type and animal_type.lower() == candidate.animal_type.lower():
                        score += 0.2
                    # порода (вес 0.15)
                    if breed and candidate.breed:
                        score += 0.15 * normalized_similarity(breed, candidate.breed)
                    # окрас (вес 0.1)
                    if color and candidate.color:
                        score += 0.1 * normalized_similarity(color, candidate.color)
                    # владелец (вес 0.3)
                    if owner_full_name and candidate.owner and candidate.owner.full_name:
                        score += 0.3 * normalized_similarity(owner_full_name, candidate.owner.full_name)
                    if score > best_score:
                        best_score = score
                        best_pet = candidate

                if best_score > 0.8:
                    messages.warning(request, f'Найден похожий питомец "{best_pet.name}" (совпадение {best_score:.0%}) по кличке/владельцу/породе. Пропущено.')
                    skipped_fuzzy += 1
                else:
                    _create_pet_from_row(row)
                    created_count += 1

            messages.success(request, f'Импорт питомцев завершён: создано {created_count}, пропущено по чипу {skipped_chip}, пропущено по нечёткому совпадению {skipped_fuzzy}')

        elif import_type == 'visits':
            created_count = 0
            errors = []
            for row in reader:
                chip = row.get('chip_number', '').strip()
                if not chip:
                    errors.append('Отсутствует номер чипа в строке')
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

                employee_name = row.get('employee_name', '').strip()
                employee = None
                if employee_name:
                    emp_qs = Employee.objects.filter(full_name__icontains=employee_name)
                    if emp_qs.exists():
                        employee = emp_qs.first()
                    else:
                        errors.append(f'Сотрудник "{employee_name}" не найден, визит сохранён без врача')

                Visit.objects.create(
                    pet=pet,
                    clinic=clinic,
                    employee=employee,
                    date=row.get('date'),
                    diagnosis=row.get('diagnosis', ''),
                    treatment=row.get('treatment', ''),
                    cost=row.get('cost', 0)
                )
                created_count += 1

            messages.success(request, f'Импорт визитов завершён: добавлено {created_count} визитов.')
            if errors:
                messages.warning(request, f'Предупреждения: {", ".join(errors[:5])}')

        return redirect('import_data')

    return render(request, 'core/import.html')

# ========== ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ СОЗДАНИЯ ПИТОМЦА ==========
def _create_pet_from_row(row):
    """Создаёт питомца из строки CSV, также создаёт/находит владельца и клинику"""
    # Владелец
    owner_full_name = row.get('owner_name', '').strip()
    owner = None
    if owner_full_name:
        owner, _ = Owner.objects.get_or_create(full_name=owner_full_name)
    # Клиника
    clinic_name = row.get('clinic_name', '').strip()
    clinic, _ = Clinic.objects.get_or_create(name=clinic_name)
    # Чип
    chip = row.get('chip_number', '').strip() or None
    # Дата рождения (если есть)
    birth_date = row.get('birth_date', '').strip()
    birth_date = birth_date if birth_date else None
    # Возраст (если нет даты рождения)
    age = row.get('age', '').strip()
    age = int(age) if age.isdigit() else None

    Pet.objects.create(
        name=row.get('name', '').strip(),
        animal_type=row.get('animal_type', '').strip(),
        breed=row.get('breed', '').strip(),
        color=row.get('color', '').strip(),
        age=age,
        birth_date=birth_date,
        chip_number=chip,
        owner=owner,
        clinic=clinic,
    )