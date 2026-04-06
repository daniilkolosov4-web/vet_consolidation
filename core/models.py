from django.db import models

class Clinic(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название клиники")
    address = models.TextField(blank=True, verbose_name="Адрес")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Клиника"
        verbose_name_plural = "Клиники"

class Pet(models.Model):
    name = models.CharField(max_length=100, verbose_name="Кличка")
    animal_type = models.CharField(max_length=50, verbose_name="Вид (собака, кошка и т.д.)")
    age = models.IntegerField(null=True, blank=True, verbose_name="Возраст")
    owner_name = models.CharField(max_length=200, verbose_name="Владелец")
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name="pets", verbose_name="Клиника")

    def __str__(self):
        return f"{self.name} ({self.animal_type})"

    class Meta:
        verbose_name = "Животное"
        verbose_name_plural = "Животные"

class Visit(models.Model):
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name="visits", verbose_name="Животное")
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name="visits", verbose_name="Клиника")
    date = models.DateField(verbose_name="Дата приёма")
    diagnosis = models.CharField(max_length=300, verbose_name="Диагноз")
    treatment = models.TextField(blank=True, verbose_name="Назначения")
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Стоимость")

    def __str__(self):
        return f"{self.date} – {self.pet.name} – {self.diagnosis}"

    class Meta:
        verbose_name = "Визит"
        verbose_name_plural = "Визиты"