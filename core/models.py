from django.db import models

# ========== СУЩНОСТИ ==========

class Clinic(models.Model):
    """Ветеринарная клиника"""
    name = models.CharField(max_length=200, verbose_name="Название клиники")
    address = models.TextField(blank=True, verbose_name="Адрес")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Клиника"
        verbose_name_plural = "Клиники"


class Owner(models.Model):
    """Владелец животного"""
    full_name = models.CharField(max_length=200, verbose_name="ФИО")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    address = models.TextField(blank=True, verbose_name="Адрес")
    email = models.EmailField(blank=True, verbose_name="Email")

    def __str__(self):
        return self.full_name

    class Meta:
        verbose_name = "Владелец"
        verbose_name_plural = "Владельцы"


class Employee(models.Model):
    """Сотрудник клиники (ветеринар)"""
    full_name = models.CharField(max_length=200, verbose_name="ФИО")
    position = models.CharField(max_length=100, verbose_name="Должность")
    specialization = models.CharField(max_length=100, blank=True, verbose_name="Специализация")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")

    def __str__(self):
        return f"{self.full_name} ({self.position})"

    class Meta:
        verbose_name = "Специалист"
        verbose_name_plural = "Специалисты"


class Pet(models.Model):
    """Животное (питомец)"""
    name = models.CharField(max_length=100, verbose_name="Кличка")
    animal_type = models.CharField(max_length=50, verbose_name="Вид (собака, кошка и т.д.)")
    breed = models.CharField(max_length=100, blank=True, verbose_name="Порода")
    color = models.CharField(max_length=50, blank=True, verbose_name="Окрас")
    birth_date = models.DateField(null=True, blank=True, verbose_name="Дата рождения")
    age = models.IntegerField(null=True, blank=True, verbose_name="Возраст (лет)")
    chip_number = models.CharField(
        max_length=15,
        unique=True,
        null=True,
        blank=True,
        verbose_name="Номер чипа",
        help_text="Уникальный 15-значный номер (ISO 11784/11785)"
    )
    photo = models.ImageField(
        upload_to='pet_photos/',
        null=True,
        blank=True,
        verbose_name="Фото питомца"
    )
    # Внешние ключи
    owner = models.ForeignKey(
        Owner,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pets",
        verbose_name="Владелец"
    )
    clinic = models.ForeignKey(
        Clinic,
        on_delete=models.CASCADE,
        related_name="pets",
        verbose_name="Клиника регистрации"
    )

    def __str__(self):
        return f"{self.name} ({self.animal_type})"

    class Meta:
        verbose_name = "Животное"
        verbose_name_plural = "Животные"


class Visit(models.Model):
    """Визит (приём) животного в клинике"""
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name="visits", verbose_name="Животное")
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name="visits", verbose_name="Клиника")
    employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="visits",
        verbose_name="Ветеринар"
    )
    date = models.DateField(verbose_name="Дата приёма")
    diagnosis = models.CharField(max_length=300, verbose_name="Диагноз")
    treatment = models.TextField(blank=True, verbose_name="Назначения")
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Стоимость")

    def __str__(self):
        return f"{self.date} – {self.pet.name} – {self.diagnosis}"

    class Meta:
        verbose_name = "Визит"
        verbose_name_plural = "Визиты"