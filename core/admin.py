from django.contrib import admin
from .models import Clinic, Pet, Visit

admin.site.register(Clinic)
admin.site.register(Pet)
admin.site.register(Visit)