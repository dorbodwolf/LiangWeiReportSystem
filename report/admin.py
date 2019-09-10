from django.contrib import admin

# Register your models here.
from django.contrib.gis import admin
from .models import ZengWei, FigureSpot

admin.site.register(ZengWei, admin.OSMGeoAdmin)
admin.site.register(FigureSpot, admin.OSMGeoAdmin)

