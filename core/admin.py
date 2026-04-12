from django.contrib import admin
from .models import Clinic, Pet, Visit

@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ('name', 'animal_type', 'owner_name', 'clinic', 'chip_number')
    search_fields = ('chip_number', 'name', 'owner_name')
    list_filter = ('clinic', 'animal_type')

admin.site.register(Clinic)
admin.site.register(Visit)