from django.shortcuts import render, redirect
from .models import Visit, Clinic
from .forms import VisitForm

def index(request):
    clinic_id = request.GET.get('clinic')
    visits = Visit.objects.all().select_related('clinic', 'pet')
    if clinic_id:
        visits = visits.filter(clinic_id=clinic_id)
    clinics = Clinic.objects.all()
    return render(request, 'core/index.html', {'visits': visits, 'clinics': clinics})

def add_visit(request):
    if request.method == 'POST':
        form = VisitForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = VisitForm()
    return render(request, 'core/add_visit.html', {'form': form})