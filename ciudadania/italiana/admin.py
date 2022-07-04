from django.contrib import admin as dj_admin
from django_neomodel import admin as neo_admin

from .models import Person

# Register your models here.
class PersonAdmin(dj_admin.ModelAdmin):
    list_display = ("name", "family_uuid", "birthday", "has_citizenship")
    ordering = ("family_uuid", "birthday")

neo_admin.register(Person, PersonAdmin)