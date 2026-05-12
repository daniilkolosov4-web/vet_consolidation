import random
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vet_system.settings')
django.setup()

from core.models import Pet, Clinic, Employee

pets = list(Pet.objects.all())
clinics = list(Clinic.objects.all())
employees = list(Employee.objects.all())
if not employees:
    Employee.objects.create(full_name='Тестовый врач', position='ветеринар')
    employees = list(Employee.objects.all())

visits_created = 0
for pet in pets:
    num = random.randint(0, 3)
    for _ in range(num):
        clinic = random.choice(clinics)
        employee = random.choice(employees)
        date = f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
        diagnosis = random.choice(['ОК', 'Гастрит', 'Травма', 'Прививка', 'Аллергия'])
        treatment = 'Назначено лечение'
        cost = random.randint(500, 5000)
        pet.visits.create(
            clinic=clinic,
            employee=employee,
            date=date,
            diagnosis=diagnosis,
            treatment=treatment,
            cost=cost
        )
        visits_created += 1

print(f"Создано {visits_created} визитов")