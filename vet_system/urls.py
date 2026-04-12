from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from core import views

urlpatterns = [
    path('', views.index, name='index'),
    path('admin/', admin.site.urls),
    path('add/', views.add_visit, name='add_visit'),
    path('pet/<int:pk>/', views.pet_detail, name='pet_detail'),
    path('import/', views.import_data, name='import_data'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)