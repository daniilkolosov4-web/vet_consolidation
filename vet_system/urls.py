from django.contrib import admin
from django.urls import path, include
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('add/', views.add_visit, name='add_visit'),
    path('pet/<int:pk>/', views.pet_detail, name='pet_detail'),
    path('import/', views.import_data, name='import_data'),
    path('import/map/', views.map_columns, name='map_columns'),
    path('import/execute/', views.execute_import, name='execute_import'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('export/', views.export_visits_csv, name='export_visits'),
]