import os
import urllib.parse
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from .backend import process_answers  # Backend logic import
from .models import StudentResult     # Database model import

def result_view(request):
    if request.method == 'POST':
        # 1. Get the uploaded files
        student_file = request.FILES.get('file')
        model_answers_file = request.FILES.get('model_answers')

        # 2. Check if both files were uploaded
        if not student_file or not model_answers_file:
            return render(request, 'form.html', {'error': 'Please upload both files.'})

        # 3. Create temp directory
        upload_dir = 'temp'
        os.makedirs(upload_dir, exist_ok=True)

        # 4. Sanitize and define paths
        sanitized_student_name = urllib.parse.quote(student_file.name)
        sanitized_model_name = urllib.parse.quote(model_answers_file.name)

        student_file_path = os.path.join(upload_dir, sanitized_student_name)
        model_answers_file_path = os.path.join(upload_dir, sanitized_model_name)

        # 5. Save files to the actual paths
        fs = FileSystemStorage(location=upload_dir)
        if not fs.exists(sanitized_student_name):
            fs.save(sanitized_student_name, student_file)
        if not fs.exists(sanitized_model_name):
            fs.save(sanitized_model_name, model_answers_file)

        # 6. Call process_answers (Ab paths sahi milenge)
        results, total_marks = process_answers(student_file_path, model_answers_file_path)

        # 7. Percentage nikalna
        # Maan lete hain har question 10 marks ka hai
        max_possible = len(results) * 10
        perc = (total_marks / max_possible) * 100 if max_possible > 0 else 0

        # 8. SQL ME DATA SAVE KAREIN
        StudentResult.objects.create(
            student_name=student_file.name, 
            total_marks=total_marks,
            percentage=round(perc, 2)
        )

        # 9. Result page dikhayein
        return render(request, 'results.html', {
            'total_marks': total_marks,
            'results': results,
            'percentage': round(perc, 2)
        })

    return render(request, 'form.html')

# --- Baki ke views ---

def history_view(request):
    """Teacher dashboard ke liye records"""
    records = StudentResult.objects.all().order_by('-date_analyzed')
    return render(request, 'history.html', {'records': records})

def home_view(req):
    return render(req, 'home.html')

def form_view(req): 
    return render(req, 'form.html')

def feature_view(req):
    return render(req, 'features.html')

def about_view(req):
    return render(req, 'about.html')

def contact_view(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        print(f"Contact from {name}: {message}") # Debugging ke liye
    return render(request, 'contact.html')