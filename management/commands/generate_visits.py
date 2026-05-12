import random
import csv
from django.core.management.base import BaseCommand
from core.models import Pet, Clinic, Employee

class Command(BaseCommand):
    help = 'Generates test visits for existing pets'

    def handle(self, *args, **options):
        pets = list(Pet.objects.all())
        clinics = list(Clinic.objects.all())
        employees = list(Employee.objects.all())
        if not employees:
            # если нет сотрудников – создадим одного
            emp = Employee.objects.create(full_name='Тестовый врач', position='ветеринар')
            employees = [emp]

        visits_data = []
        for pet in pets:
            # генерируем от 0 до 3 визитов на питомца
            num_visits = random.randint(0, 3)
            for _ in range(num_visits):
                clinic = random.choice(clinics)
                employee = random.choice(employees)
                date = f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
                diagnosis = random.choice(['ОК', 'Гастрит', 'Травма', 'Прививка', 'Аллергия'])
                treatment = 'Назначено лечение'
                cost = random.randint(500, 5000)
                visits_data.append({
                    'chip_number': pet.chip_number,
                    'clinic_name': clinic.name,
                    'employee_name': employee.full_name,
                    'date': date,
                    'diagnosis': diagnosis,
                    'treatment': treatment,
                    'cost': cost,
                })

        # Запись в CSV
        with open('test_visits.csv', 'w', newline='', encoding='utf-8-sig') as f:
            fieldnames = ['chip_number', 'clinic_name', 'employee_name', 'date', 'diagnosis', 'treatment', 'cost']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(visits_data)

        self.stdout.write(self.style.SUCCESS(f'Сгенерировано {len(visits_data)} визитов в test_visits.csv'))