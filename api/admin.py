from django.contrib import admin

from api.models.category import Category
from api.models.company import Company

admin.site.register(Category)
admin.site.register(Company)
