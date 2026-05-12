from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from .models import Visit, Clinic, Pet, Owner, Employee
from .forms import VisitForm, ChipSearchForm
import csv
import io
import tempfile
import os

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

@login_required
def index(request):
    clinic_id = request.GET.get('clinic')
    visits = Visit.objects.all().select_related('clinic', 'pet', 'pet__owner', 'employee')
    if clinic_id:
        visits = visits.filter(clinic_id=clinic_id)
    clinics = Clinic.objects.all()

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

@login_required
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

@login_required
def pet_detail(request, pk):
    pet = get_object_or_404(Pet, pk=pk)
    visits = pet.visits.all().select_related('clinic', 'employee').order_by('-date')
    return render(request, 'core/pet_detail.html', {'pet': pet, 'visits': visits})

# ========== ИМПОРТ С МАППИНГОМ (3 ЭТАПА) ==========

@user_passes_test(lambda u: u.groups.filter(name='Manager').exists())
@login_required
def import_data(request):
    """Шаг 1: загрузка CSV файла и выбор типа импорта"""
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        import_type = request.POST.get('import_type')

        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'Файл должен быть в формате CSV')
            return redirect('import_data')

        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f'import_{import_type}_{request.user.id}.csv')
        with open(temp_path, 'wb') as f:
            for chunk in csv_file.chunks():
                f.write(chunk)

        try:
            with open(temp_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                headers = next(reader)
        except UnicodeDecodeError:
            with open(temp_path, 'r', encoding='cp1251') as f:
                reader = csv.reader(f)
                headers = next(reader)

        request.session['import_file_path'] = temp_path
        request.session['import_type'] = import_type
        request.session['headers'] = headers

        return redirect('map_columns')

    return render(request, 'core/import.html')

@user_passes_test(lambda u: u.groups.filter(name='Manager').exists())
@login_required
def map_columns(request):
    """Шаг 2: сопоставление колонок CSV с полями модели"""
    import_type = request.session.get('import_type')
    headers = request.session.get('headers')
    if not headers or not import_type:
        messages.error(request, 'Сессия устарела, загрузите файл заново')
        return redirect('import_data')

    if import_type == 'pets':
        fields = [
            ('name', 'Кличка'),
            ('animal_type', 'Вид'),
            ('breed', 'Порода'),
            ('color', 'Окрас'),
            ('owner_name', 'ФИО владельца'),
            ('clinic_name', 'Название клиники'),
            ('chip_number', 'Номер чипа'),
            ('birth_date', 'Дата рождения (ГГГГ-ММ-ДД)'),
            ('age', 'Возраст (лет)'),
        ]
    else:  # visits
        fields = [
            ('chip_number', 'Номер чипа'),
            ('clinic_name', 'Название клиники'),
            ('employee_name', 'ФИО врача'),
            ('date', 'Дата приёма'),
            ('diagnosis', 'Диагноз'),
            ('treatment', 'Назначения'),
            ('cost', 'Стоимость'),
        ]

    if request.method == 'POST':
        mapping = {}
        for field, _ in fields:
            col = request.POST.get(f'field_{field}')
            if col:
                mapping[field] = col
        request.session['mapping'] = mapping
        return redirect('execute_import')

    return render(request, 'core/map_columns.html', {
        'headers': headers,
        'fields': fields,
        'import_type': import_type,
    })

@user_passes_test(lambda u: u.groups.filter(name='Manager').exists())
@login_required
def execute_import(request):
    """Шаг 3: выполнение импорта с использованием маппинга"""
    import_type = request.session.get('import_type')
    file_path = request.session.get('import_file_path')
    mapping = request.session.get('mapping')

    if not all([import_type, file_path, mapping]):
        messages.error(request, 'Данные сессии утеряны, начните импорт заново')
        return redirect('import_data')

    rows = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                mapped_row = {}
                for model_field, csv_col in mapping.items():
                    mapped_row[model_field] = row.get(csv_col, '').strip()
                rows.append(mapped_row)
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='cp1251') as f:
            reader = csv.DictReader(f)
            for row in reader:
                mapped_row = {}
                for model_field, csv_col in mapping.items():
                    mapped_row[model_field] = row.get(csv_col, '').strip()
                rows.append(mapped_row)

    if import_type == 'pets':
        created_count = 0
        skipped_chip = 0
        skipped_fuzzy = 0
        for row in rows:
            chip = row.get('chip_number', '')
            if chip:
                if Pet.objects.filter(chip_number=chip).exists():
                    skipped_chip += 1
                    continue
                else:
                    _create_pet_from_row(row)
                    created_count += 1
                    continue

            name = row.get('name', '')
            animal_type = row.get('animal_type', '')
            breed = row.get('breed', '')
            color = row.get('color', '')
            owner_full_name = row.get('owner_name', '')

            candidates = Pet.objects.filter(animal_type=animal_type) if animal_type else Pet.objects.all()
            best_score = 0.0
            best_pet = None
            for candidate in candidates:
                score = 0.0
                if name and candidate.name:
                    score += 0.25 * normalized_similarity(name, candidate.name)
                if animal_type and candidate.animal_type and animal_type.lower() == candidate.animal_type.lower():
                    score += 0.2
                if breed and candidate.breed:
                    score += 0.15 * normalized_similarity(breed, candidate.breed)
                if color and candidate.color:
                    score += 0.1 * normalized_similarity(color, candidate.color)
                if owner_full_name and candidate.owner and candidate.owner.full_name:
                    score += 0.3 * normalized_similarity(owner_full_name, candidate.owner.full_name)
                if score > best_score:
                    best_score = score
                    best_pet = candidate
            if best_score > 0.8:
                messages.warning(request, f'Найден похожий питомец "{best_pet.name}" (совпадение {best_score:.0%}). Пропущено.')
                skipped_fuzzy += 1
            else:
                _create_pet_from_row(row)
                created_count += 1

        messages.success(request, f'Импорт питомцев: создано {created_count}, пропущено по чипу {skipped_chip}, пропущено по нечёткому совпадению {skipped_fuzzy}')

    else:  # visits
        created_count = 0
        errors = []
        for row in rows:
            chip = row.get('chip_number', '')
            if not chip:
                errors.append('Отсутствует номер чипа')
                continue
            try:
                pet = Pet.objects.get(chip_number=chip)
            except Pet.DoesNotExist:
                errors.append(f'Питомец с чипом {chip} не найден')
                continue

            clinic_name = row.get('clinic_name', '')
            try:
                clinic = Clinic.objects.get(name=clinic_name)
            except Clinic.DoesNotExist:
                errors.append(f'Клиника "{clinic_name}" не найдена')
                continue

            employee_name = row.get('employee_name', '')
            employee = None
            if employee_name:
                emp_qs = Employee.objects.filter(full_name__icontains=employee_name)
                if emp_qs.exists():
                    employee = emp_qs.first()
                else:
                    errors.append(f'Сотрудник "{employee_name}" не найден, визит без врача')

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

        messages.success(request, f'Импорт визитов: добавлено {created_count} визитов.')
        if errors:
            messages.warning(request, f'Предупреждения: {", ".join(errors[:5])}')

    if os.path.exists(file_path):
        os.remove(file_path)
    for key in ['import_file_path', 'import_type', 'mapping', 'headers']:
        if key in request.session:
            del request.session[key]

    return redirect('index')

# ========== ЭКСПОРТ CSV ==========
@login_required
def export_visits_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="visits_export.csv"'
    writer = csv.writer(response)
    writer.writerow(['Дата', 'Клиника', 'Питомец', 'Вид', 'Порода', 'Окрас', 'Владелец', 'Чип', 'Диагноз', 'Лечение', 'Стоимость'])

    visits = Visit.objects.all().select_related('clinic', 'pet', 'pet__owner', 'employee')
    for visit in visits:
        writer.writerow([
            visit.date,
            visit.clinic.name,
            visit.pet.name,
            visit.pet.animal_type,
            visit.pet.breed or '',
            visit.pet.color or '',
            visit.pet.owner.full_name if visit.pet.owner else '',
            visit.pet.chip_number or '',
            visit.diagnosis,
            visit.treatment,
            visit.cost,
        ])
    return response

# ========== ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ СОЗДАНИЯ ПИТОМЦА ==========
def _create_pet_from_row(row):
    owner_full_name = row.get('owner_name', '').strip()
    owner = None
    if owner_full_name:
        owner, _ = Owner.objects.get_or_create(full_name=owner_full_name)

    clinic_name = row.get('clinic_name', '').strip()
    clinic, _ = Clinic.objects.get_or_create(name=clinic_name)

    chip = row.get('chip_number', '').strip() or None
    birth_date = row.get('birth_date', '').strip()
    birth_date = birth_date if birth_date else None
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