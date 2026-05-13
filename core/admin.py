from django.contrib import admin
from .models import Clinic, Owner, Employee, Pet, Visit

@admin.register(Clinic)
class ClinicAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'phone')
    search_fields = ('name', 'phone')

@admin.register(Owner)
class OwnerAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'phone', 'email', 'is_active')
    search_fields = ('full_name', 'phone', 'email')
    list_filter = ('is_active',)   # <-- фильтр по активности

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'position', 'specialization', 'phone', 'is_active')
    search_fields = ('full_name', 'position', 'specialization')
    list_filter = ('is_active',)   # <-- фильтр по активности

@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'animal_type', 'breed', 'color', 
        'owner', 'clinic', 'chip_number', 'get_age'
    )
    search_fields = ('chip_number', 'name', 'owner__full_name', 'breed')
    list_filter = ('animal_type', 'clinic', 'breed')
    raw_id_fields = ('owner', 'clinic')
    autocomplete_fields = ('owner', 'clinic')

    def get_age(self, obj):
        return obj.get_age()
    get_age.short_description = 'Возраст (лет)'

@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'pet', 'clinic', 'employee', 'diagnosis', 'cost')
    search_fields = ('pet__name', 'diagnosis', 'pet__chip_number')
    list_filter = ('date', 'clinic', 'employee')
    raw_id_fields = ('pet', 'clinic', 'employee')
    date_hierarchy = 'date'