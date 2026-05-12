from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from core.models import Pet, Visit, Owner, Clinic

class Command(BaseCommand):
    help = 'Создаёт группы Doctor и Manager и назначает права'

    def handle(self, *args, **options):
        # Группа Doctor (ветеринар) – полные права на добавление/изменение
        doctor_group, _ = Group.objects.get_or_create(name='Doctor')
        # Группа Manager (администратор клиники) – только импорт и просмотр
        manager_group, _ = Group.objects.get_or_create(name='Manager')

        # Получаем все разрешения для моделей
        models = [Pet, Visit, Owner, Clinic]
        for model in models:
            ct = ContentType.objects.get_for_model(model)
            # Взятие всех разрешений (add, change, delete, view)
            perms = Permission.objects.filter(content_type=ct)
            doctor_group.permissions.add(*perms)

            # Менеджер: только просмотр (view) и добавление (add) – но не изменение/удаление
            view_perm = Permission.objects.get(codename=f'view_{model._meta.model_name}', content_type=ct)
            add_perm = Permission.objects.get(codename=f'add_{model._meta.model_name}', content_type=ct)
            manager_group.permissions.add(view_perm, add_perm)

        self.stdout.write(self.style.SUCCESS('Группы Doctor и Manager созданы, права назначены'))