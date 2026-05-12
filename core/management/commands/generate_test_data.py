import random
import csv
from django.core.management.base import BaseCommand
from core.models import Pet, Owner, Clinic

class Command(BaseCommand):
    help = 'Generates synthetic test data (pets) for experiment'

    def handle(self, *args, **options):
        # Список видов, пород, окрасов, кличек, фамилий владельцев
        animal_types = ['собака', 'кошка', 'хомяк', 'попугай', 'рептилия']
        dog_breeds = ['лабрадор', 'овчарка', 'спаниель', 'такса', 'бульдог', 'пудель', 'ротвейлер', 'хаски']
        cat_breeds = ['сиамская', 'персидская', 'мейн-кун', 'сфинкс', 'британская']
        colors = ['чёрный', 'белый', 'рыжий', 'серый', 'коричневый', 'пятнистый', 'полосатый']
        names = ['Барсик', 'Мурка', 'Шарик', 'Жучка', 'Рекс', 'Симба', 'Луна', 'Белка', 'Тимон', 'Пумба']
        owners = ['Иванов И.И.', 'Петров П.П.', 'Сидоров С.С.', 'Кузнецова А.В.', 'Смирнов Д.А.', 'Васильева Е.Н.',
                  'Фёдоров К.Р.', 'Морозова О.Л.', 'Волков В.В.', 'Алексеева Т.П.']

        clinics = list(Clinic.objects.all())
        if not clinics:
            clinic = Clinic.objects.create(name='Тестовая клиника')
            clinics = [clinic]

        total_pets = 2000
        duplicate_ratio = 0.2  # 20% дубликатов
        chip_ratio = 0.3  # 30% животных с чипом

        pets_data = []
        # Генерация исходных записей
        for i in range(total_pets):
            animal_type = random.choice(animal_types)
            if animal_type == 'собака':
                breed = random.choice(dog_breeds)
            elif animal_type == 'кошка':
                breed = random.choice(cat_breeds)
            else:
                breed = ''
            color = random.choice(colors)
            name = random.choice(names)
            owner_name = random.choice(owners)
            chip = str(random.randint(10**14, 10**15 - 1)) if random.random() < chip_ratio else ''
            clinic = random.choice(clinics)

            pets_data.append({
                'name': name,
                'animal_type': animal_type,
                'breed': breed,
                'color': color,
                'owner_name': owner_name,
                'clinic_name': clinic.name,
                'chip_number': chip,
            })

        # Создание дубликатов (20% от исходных)
        duplicates_count = int(total_pets * duplicate_ratio)
        indices_to_duplicate = random.sample(range(total_pets), duplicates_count)
        for idx in indices_to_duplicate:
            orig = pets_data[idx]
            dup = orig.copy()
            # Вносим искажения: опечатка в кличке, другой владелец (но иногда тот же), другая клиника
            if random.random() < 0.5:
                # меняем последнюю букву клички
                if dup['name']:
                    dup['name'] = orig['name'][:-1] + random.choice('аоуыэ')
            if random.random() < 0.3:
                dup['owner_name'] = random.choice(owners)
            # Другая клиника (если есть несколько)
            other_clinics = [c for c in clinics if c.name != orig['clinic_name']]
            if other_clinics and random.random() < 0.5:
                dup['clinic_name'] = random.choice(other_clinics).name
            pets_data.append(dup)

        # Перемешиваем
        random.shuffle(pets_data)

        # Запись в CSV с кодировкой UTF-8-sig (добавляет BOM для совместимости с Excel)
        csv_file = 'test_pets_2000.csv'
        with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
            fieldnames = ['name', 'animal_type', 'breed', 'color', 'owner_name', 'clinic_name', 'chip_number']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(pets_data)

        self.stdout.write(self.style.SUCCESS(f'Сгенерировано {len(pets_data)} записей в {csv_file} (кодировка UTF-8)'))