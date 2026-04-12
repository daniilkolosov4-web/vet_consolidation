from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('add/', views.add_visit, name='add_visit'),
    path('pet/<int:pk>/', views.pet_detail, name='pet_detail'),
    path('import/', views.import_data, name='import_data'),
]