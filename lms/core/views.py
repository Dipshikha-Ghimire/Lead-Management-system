from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import date, timedelta
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.db.models import Sum, Count, DecimalField, Value
from django.db.models.functions import Coalesce
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from .forms import LoginForm, SignupForm
from .models import Lead, Program, Application, EntranceExam, Scholarship, Payment, Staff, Department, Notification


def _serialize_application_row(application):
    lead = application.lead
    return {
        'id': application.app_id,
        'lead_id': lead.lead_id,
        'program_id': application.program.prog_id,
        'applicant': f"{lead.first_name} {lead.last_name}",
        'email': lead.email or '—',
        'program': application.program.name,
        'status': application.get_status_display(),
        'status_key': application.status,
        'documents_url': application.documents_url or '',
        'submitted': application.app_date.strftime('%Y-%m-%d'),
    }


# ---------- AUTH VIEWS ----------

def login_view(request):
    next_url = request.POST.get('next') or request.GET.get('next')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            # If form is valid, user is already authenticated in the form's clean method
            user = form.user
            login(request, user)

            remember_me = form.cleaned_data.get('remember_me', False)
            if not remember_me:
                request.session.set_expiry(0)

            messages.success(request, f'Welcome back, {user.username}!')
            
            # Redirect to next parameter if available, else dashboard
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)

            return redirect('dashboard')
        else:
            # Display form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = LoginForm()
    
    return render(request, 'core/login.html', {'form': form, 'next': next_url})


def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            # Create the user
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password1']
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            
            messages.success(request, 'Account created successfully! Please login with your credentials.')
            return redirect('login')
        else:
            # Display form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = SignupForm()
    
    return render(request, 'core/signup.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


# ---------- PROTECTED PAGES ----------

@login_required(login_url='login')
def dashboard(request):
    now = timezone.now()
    this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
    
    total_leads = Lead.objects.count()
    qualified_leads = Lead.objects.filter(current_status='qualified').count()
    enrolled_leads = Lead.objects.filter(current_status='enrolled').count()
    reviewed_applications = Application.objects.filter(status='reviewed').count()
    accepted_applications = Application.objects.filter(status='accepted').count()
    exam_count = EntranceExam.objects.count()

    verified_revenue = Payment.objects.filter(status='verified').aggregate(
        total=Coalesce(
            Sum('amount'),
            Value(0),
            output_field=DecimalField(max_digits=10, decimal_places=2),
        )
    )['total']

    # Monthly growth calculations
    leads_this_month = Lead.objects.filter(created_at__gte=this_month_start).count()
    leads_last_month = Lead.objects.filter(created_at__gte=last_month_start, created_at__lt=this_month_start).count()
    leads_growth = ((leads_this_month - leads_last_month) / leads_last_month * 100) if leads_last_month > 0 else (100 if leads_this_month > 0 else 0)
    
    qualified_this_month = Lead.objects.filter(current_status='qualified', created_at__gte=this_month_start).count()
    qualified_last_month = Lead.objects.filter(current_status='qualified', created_at__gte=last_month_start, created_at__lt=this_month_start).count()
    qualified_growth = ((qualified_this_month - qualified_last_month) / qualified_last_month * 100) if qualified_last_month > 0 else (100 if qualified_this_month > 0 else 0)
    
    enrolled_this_month = Lead.objects.filter(current_status='enrolled', created_at__gte=this_month_start).count()
    enrolled_last_month = Lead.objects.filter(current_status='enrolled', created_at__gte=last_month_start, created_at__lt=this_month_start).count()
    enrolled_growth = ((enrolled_this_month - enrolled_last_month) / enrolled_last_month * 100) if enrolled_last_month > 0 else (100 if enrolled_this_month > 0 else 0)
    
    revenue_this_month = Payment.objects.filter(status='verified', payment_date__gte=this_month_start).aggregate(
        total=Coalesce(Sum('amount'), Value(0), output_field=DecimalField(max_digits=10, decimal_places=2))
    )['total']
    revenue_last_month = Payment.objects.filter(status='verified', payment_date__gte=last_month_start, payment_date__lt=this_month_start).aggregate(
        total=Coalesce(Sum('amount'), Value(0), output_field=DecimalField(max_digits=10, decimal_places=2))
    )['total']
    revenue_growth = float(revenue_this_month - revenue_last_month)
    if revenue_last_month > 0:
        revenue_growth_pct = (float(revenue_this_month) - float(revenue_last_month)) / float(revenue_last_month) * 100
    else:
        revenue_growth_pct = 100 if revenue_this_month > 0 else 0

    pending_applications = Application.objects.filter(status='pending').count()
    pending_scholarships = Scholarship.objects.filter(is_approved=False).count()

    source_totals = Lead.objects.values('source').annotate(count=Count('lead_id')).order_by('source')
    source_data = []
    for item in source_totals:
        source_data.append({
            'label': item['source'].replace('_', ' ').title() if item['source'] else 'Other',
            'count': item['count'],
            'percent': round((item['count'] / total_leads) * 100) if total_leads else 0,
        })
    
    source_totals_json = [
        {'label': s['label'], 'count': s['count'], 'percent': s['percent']}
        for s in source_data
    ]

    recent_leads_qs = Lead.objects.order_by('-created_at')[:5]
    recent_leads = []
    for lead in recent_leads_qs:
        latest_application = lead.applications.select_related('program').order_by('-app_date').first()
        recent_leads.append(
            {
                'name': f"{lead.first_name} {lead.last_name}",
                'program': latest_application.program.name if latest_application else '—',
                'stage': lead.get_current_status_display(),
                'date': lead.created_at,
            }
        )

    context = {
        'total_leads': total_leads,
        'leads_growth': int(leads_growth),
        'leads_this_month': leads_this_month,
        'qualified_leads': qualified_leads,
        'qualified_growth': int(qualified_growth),
        'qualified_this_month': qualified_this_month,
        'enrolled_count': enrolled_leads,
        'enrolled_growth': int(enrolled_growth),
        'enrolled_this_month': enrolled_this_month,
        'verified_revenue': verified_revenue,
        'revenue_growth': int(revenue_growth_pct),
        'revenue_this_month': revenue_this_month,
        'pending_applications': pending_applications,
        'pending_scholarships': pending_scholarships,
        'funnel_capture': total_leads,
        'funnel_qualification': qualified_leads,
        'funnel_review': reviewed_applications,
        'funnel_exam': exam_count,
        'funnel_enrolled': accepted_applications,
        'source_totals': source_data,
        'source_totals_json': source_totals_json,
        'recent_leads': recent_leads,
    }

    return render(request, 'core/dashboard.html', context)


@login_required(login_url='login')
def leads(request):
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    
    leads_qs = Lead.objects.all().prefetch_related('applications__program').order_by('-created_at')
    
    if status_filter:
        leads_qs = leads_qs.filter(current_status=status_filter)

    if query:
        leads_qs = leads_qs.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
            | Q(current_status__icontains=query)
            | Q(program_interest__icontains=query)
        )

    lead_rows = []
    for lead in leads_qs:
        applications = list(lead.applications.all())
        approved_app = None
        for app in applications:
            if app.status == 'accepted':
                approved_app = app
                break
        if not approved_app:
            approved_app = applications[0] if applications else None
        
        program_name = lead.program_interest or (approved_app.program.name if approved_app and approved_app.program else '—')
        
        lead_rows.append(
            {
                'id': lead.lead_id,
                'name': f"{lead.first_name} {lead.last_name}",
                'email': lead.email or '—',
                'phone': lead.phone or '—',
                'program': program_name,
                'date_captured': lead.created_at.strftime('%Y-%m-%d'),
                'status': lead.get_current_status_display(),
                'status_key': lead.current_status,
                'date_of_birth': lead.date_of_birth.strftime('%Y-%m-%d') if lead.date_of_birth else '',
                'gender': lead.get_gender_display() if lead.gender else '',
                'address': lead.address or '',
                'nationality': lead.nationality or '',
                'alternate_contact': lead.alternate_contact or '',
                'desired_intake_year': lead.desired_intake_year or '',
                'intake_semester': lead.get_intake_semester_display() if lead.intake_semester else '',
                'highest_education_level': lead.get_highest_education_level_display() if lead.highest_education_level else '',
                'gpa_or_percentage': lead.gpa_or_percentage or '',
                'previous_institution': lead.previous_institution or '',
                'scholarship_interest': lead.get_scholarship_interest_display() if lead.scholarship_interest else '',
                'preferred_study_mode': lead.get_preferred_study_mode_display() if lead.preferred_study_mode else '',
                'source': lead.get_source_display() if lead.source else '',
                'lead_status': lead.get_current_status_display(),
                'assigned_counselor': lead.assigned_staff.full_name if lead.assigned_staff else '',
                'followup_date': lead.followup_date.strftime('%Y-%m-%d') if lead.followup_date else '',
                'notes': lead.notes or '',
                'created_at': lead.created_at,
            }
        )

    status_choices = Lead.STATUS_CHOICES
    source_choices = Lead.SOURCE_CHOICES
    counselor_choices = Staff.objects.filter(role='counselor').order_by('full_name')
    if not counselor_choices.exists():
        counselor_choices = Staff.objects.all().order_by('full_name')

    current_year = date.today().year
    intake_year_choices = [current_year + offset for offset in range(4)]
    program_choices = Program.objects.select_related('dept').order_by('dept__name', 'name')

    return render(request, 'core/leads.html', {
        'lead_rows': lead_rows,
        'query': query,
        'status_filter': status_filter,
        'status_choices': status_choices,
        'source_choices': source_choices,
        'gender_choices': Lead.GENDER_CHOICES,
        'intake_semester_choices': Lead.INTAKE_SEMESTER_CHOICES,
        'education_level_choices': Lead.EDUCATION_LEVEL_CHOICES,
        'scholarship_choices': Lead.SCHOLARSHIP_INTEREST_CHOICES,
        'study_mode_choices': Lead.STUDY_MODE_CHOICES,
        'counselor_choices': counselor_choices,
        'intake_year_choices': intake_year_choices,
        'program_choices': program_choices,
    })


@login_required(login_url='login')
@require_http_methods(["GET"])
def lead_detail_api(request, lead_id):
    lead = get_object_or_404(Lead, lead_id=lead_id)
    return JsonResponse({
        'success': True,
        'lead': {
            'lead_id': lead.lead_id,
            'first_name': lead.first_name,
            'last_name': lead.last_name,
            'email': lead.email or '',
            'phone': lead.phone or '',
            'date_of_birth': lead.date_of_birth.isoformat() if lead.date_of_birth else '',
            'gender': lead.gender or '',
            'gender_label': lead.get_gender_display() if lead.gender else '',
            'address': lead.address or '',
            'nationality': lead.nationality or '',
            'alternate_contact': lead.alternate_contact or '',
            'desired_intake_year': lead.desired_intake_year or '',
            'intake_semester': lead.intake_semester or '',
            'intake_semester_label': lead.get_intake_semester_display() if lead.intake_semester else '',
            'highest_education_level': lead.highest_education_level or '',
            'highest_education_level_label': lead.get_highest_education_level_display() if lead.highest_education_level else '',
            'gpa_or_percentage': lead.gpa_or_percentage or '',
            'previous_institution': lead.previous_institution or '',
            'scholarship_interest': lead.scholarship_interest or '',
            'scholarship_interest_label': lead.get_scholarship_interest_display() if lead.scholarship_interest else '',
            'preferred_study_mode': lead.preferred_study_mode or '',
            'preferred_study_mode_label': lead.get_preferred_study_mode_display() if lead.preferred_study_mode else '',
            'source': lead.source,
            'source_label': lead.get_source_display(),
            'current_status': lead.current_status,
            'current_status_label': lead.get_current_status_display(),
            'program_interest': lead.program_interest or '',
            'followup_date': lead.followup_date.isoformat() if lead.followup_date else '',
            'assigned_staff_id': lead.assigned_staff.staff_id if lead.assigned_staff else '',
            'assigned_staff_name': lead.assigned_staff.full_name if lead.assigned_staff else '',
            'notes': lead.notes or '',
            'created_at': lead.created_at.strftime('%Y-%m-%d %H:%M'),
        },
    })


@login_required(login_url='login')
@require_http_methods(["POST"])
def lead_update_api(request, lead_id):
    lead = get_object_or_404(Lead, lead_id=lead_id)

    def parse_optional_date(date_value):
        parsed_value = (date_value or '').strip()
        if not parsed_value:
            return None
        try:
            return date.fromisoformat(parsed_value)
        except ValueError:
            return None

    first_name = (request.POST.get('first_name') or '').strip()
    last_name = (request.POST.get('last_name') or '').strip()
    if not first_name or not last_name:
        return JsonResponse({'success': False, 'error': 'First and last name are required.'}, status=400)

    status_value = (request.POST.get('current_status') or '').strip()
    if status_value and status_value not in dict(Lead.STATUS_CHOICES):
        return JsonResponse({'success': False, 'error': 'Invalid status selected.'}, status=400)

    source_value = (request.POST.get('source') or '').strip()
    if source_value and source_value not in dict(Lead.SOURCE_CHOICES):
        source_value = 'other'

    gender_value = (request.POST.get('gender') or '').strip()
    if gender_value and gender_value not in dict(Lead.GENDER_CHOICES):
        return JsonResponse({'success': False, 'error': 'Invalid gender selected.'}, status=400)

    intake_semester_value = (request.POST.get('intake_semester') or '').strip()
    if intake_semester_value and intake_semester_value not in dict(Lead.INTAKE_SEMESTER_CHOICES):
        return JsonResponse({'success': False, 'error': 'Invalid intake semester selected.'}, status=400)

    education_value = (request.POST.get('highest_education_level') or '').strip()
    if education_value and education_value not in dict(Lead.EDUCATION_LEVEL_CHOICES):
        return JsonResponse({'success': False, 'error': 'Invalid education level selected.'}, status=400)

    scholarship_value = (request.POST.get('scholarship_interest') or '').strip()
    if scholarship_value and scholarship_value not in dict(Lead.SCHOLARSHIP_INTEREST_CHOICES):
        return JsonResponse({'success': False, 'error': 'Invalid scholarship option selected.'}, status=400)

    study_mode_value = (request.POST.get('preferred_study_mode') or '').strip()
    if study_mode_value and study_mode_value not in dict(Lead.STUDY_MODE_CHOICES):
        return JsonResponse({'success': False, 'error': 'Invalid study mode selected.'}, status=400)

    intake_year_raw = (request.POST.get('desired_intake_year') or '').strip()
    intake_year = int(intake_year_raw) if intake_year_raw.isdigit() else None

    counselor_id = (request.POST.get('assigned_staff_id') or '').strip()
    assigned_staff = None
    if counselor_id.isdigit():
        assigned_staff = Staff.objects.filter(staff_id=int(counselor_id)).first()

    lead.first_name = first_name
    lead.last_name = last_name
    lead.email = (request.POST.get('email') or '').strip() or None
    lead.phone = (request.POST.get('phone') or '').strip() or None
    lead.date_of_birth = parse_optional_date(request.POST.get('date_of_birth'))
    lead.gender = gender_value or None
    lead.address = (request.POST.get('address') or '').strip() or None
    lead.nationality = (request.POST.get('nationality') or '').strip() or None
    lead.alternate_contact = (request.POST.get('alternate_contact') or '').strip() or None
    lead.program_interest = (request.POST.get('program_interest') or '').strip() or None
    lead.desired_intake_year = intake_year
    lead.intake_semester = intake_semester_value or None
    lead.highest_education_level = education_value or None
    lead.gpa_or_percentage = (request.POST.get('gpa_or_percentage') or '').strip() or None
    lead.previous_institution = (request.POST.get('previous_institution') or '').strip() or None
    lead.scholarship_interest = scholarship_value or None
    lead.preferred_study_mode = study_mode_value or None
    lead.followup_date = parse_optional_date(request.POST.get('followup_date'))
    lead.assigned_staff = assigned_staff
    lead.notes = (request.POST.get('notes') or '').strip() or None
    if status_value:
        lead.current_status = status_value
    if source_value:
        lead.source = source_value
    lead.save()

    return JsonResponse({
        'success': True,
        'lead': {
            'lead_id': lead.lead_id,
            'name': f"{lead.first_name} {lead.last_name}",
            'email': lead.email or '—',
            'phone': lead.phone or '—',
            'status': lead.get_current_status_display(),
            'status_key': lead.current_status,
            'program_interest': lead.program_interest or '—',
            'source': lead.get_source_display(),
            'intake': (
                f"{lead.desired_intake_year} - {lead.get_intake_semester_display()}"
                if lead.desired_intake_year and lead.intake_semester
                else (str(lead.desired_intake_year) if lead.desired_intake_year else '—')
            ),
            'counselor': lead.assigned_staff.full_name if lead.assigned_staff else '—',
        },
    })


@login_required(login_url='login')
@require_http_methods(["POST"])
def lead_delete_api(request, lead_id):
    lead = get_object_or_404(Lead, lead_id=lead_id)
    lead.delete()
    return JsonResponse({'success': True})


@login_required(login_url='login')
def lead_form(request):
    if request.method == 'POST':
        source_aliases = {
            'Social Media': 'social_media',
            'Google Search': 'google_search',
            'Referral': 'referral',
            'Education Fair': 'education_fair',
            'Walk-In': 'walk_in',
            'Advertisement': 'advertisement',
            'Website': 'website',
            'Alumni': 'alumni',
        }

        source_value = (request.POST.get('lead_source') or '').strip()
        source_value = source_aliases.get(source_value, source_value)
        if source_value not in dict(Lead.SOURCE_CHOICES):
            source_value = 'other'

        gender_aliases = {
            'Male': 'male',
            'Female': 'female',
            'Prefer not to say': 'prefer_not_to_say',
        }
        intake_semester_aliases = {
            'Spring (Jan-May)': 'spring',
            'Spring (Jan–May)': 'spring',
            'Fall (Aug-Dec)': 'fall',
            'Fall (Aug–Dec)': 'fall',
            'Summer (May-Aug)': 'summer',
            'Summer (May–Aug)': 'summer',
        }
        education_aliases = {
            'High School (+2 / A-Level)': 'high_school',
            "Bachelor's Degree": 'bachelors',
            "Master's Degree": 'masters',
            'Diploma / Certificate': 'diploma_certificate',
        }
        scholarship_aliases = {
            'Yes': 'yes',
            'Yes, interested': 'yes',
            'No': 'no',
            'No, self-funded': 'no',
            'Unsure': 'unsure',
            'Not sure yet': 'unsure',
        }
        study_mode_aliases = {
            'On-campus': 'on_campus',
            'Online': 'online',
            'Hybrid': 'hybrid',
        }

        status_value = (request.POST.get('lead_status') or 'new').strip()
        if status_value not in dict(Lead.STATUS_CHOICES):
            status_value = 'new'

        first_name = (request.POST.get('first_name') or '').strip()
        last_name = (request.POST.get('last_name') or '').strip()
        if not first_name or not last_name:
            return JsonResponse({'success': False, 'error': 'First and last name are required.'}, status=400)

        counselor_name = (request.POST.get('counselor') or '').strip()
        assigned_staff = None
        if counselor_name:
            if counselor_name.isdigit():
                assigned_staff = Staff.objects.filter(staff_id=int(counselor_name)).first()
            if assigned_staff is None:
                assigned_staff = Staff.objects.filter(full_name__iexact=counselor_name).first()

        intake_year = (request.POST.get('intake_year') or '').strip()
        intake_year = int(intake_year) if intake_year.isdigit() else None

        gender_value = (request.POST.get('gender') or '').strip()
        gender_value = gender_aliases.get(gender_value, gender_value) or None

        intake_semester_value = (request.POST.get('intake_semester') or '').strip()
        intake_semester_value = intake_semester_aliases.get(intake_semester_value, intake_semester_value) or None

        education_value = (request.POST.get('education_level') or '').strip()
        education_value = education_aliases.get(education_value, education_value) or None

        scholarship_value = (request.POST.get('scholarship_interest') or '').strip()
        scholarship_value = scholarship_aliases.get(scholarship_value, scholarship_value) or None

        study_mode_value = (request.POST.get('study_mode') or '').strip()
        study_mode_value = study_mode_aliases.get(study_mode_value, study_mode_value) or None

        lead = Lead.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=(request.POST.get('email') or '').strip() or None,
            phone=(request.POST.get('phone') or '').strip() or None,
            date_of_birth=(request.POST.get('date_of_birth') or '').strip() or None,
            gender=gender_value,
            address=(request.POST.get('address') or '').strip() or None,
            nationality=(request.POST.get('nationality') or '').strip() or None,
            alternate_contact=(request.POST.get('alternate_contact') or '').strip() or None,
            program_interest=(request.POST.get('program_interest') or '').strip() or None,
            desired_intake_year=intake_year,
            intake_semester=intake_semester_value,
            highest_education_level=education_value,
            gpa_or_percentage=(request.POST.get('gpa_or_percentage') or '').strip() or None,
            previous_institution=(request.POST.get('previous_institution') or '').strip() or None,
            scholarship_interest=scholarship_value,
            preferred_study_mode=study_mode_value,
            source=source_value,
            current_status=status_value,
            followup_date=(request.POST.get('followup_date') or '').strip() or None,
            notes=(request.POST.get('notes') or '').strip() or None,
            assigned_staff=assigned_staff,
        )

        program_name = (request.POST.get('program_interest') or '').strip()
        program = None
        if program_name:
            program = Program.objects.filter(name__iexact=program_name).first()
            if not program:
                program = Program.objects.filter(name__icontains=program_name).first()
        
        application = Application.objects.create(
            lead=lead,
            program=program,
            status='pending'
        )

        Notification.objects.create(
            notification_type='new_application',
            title='New Application Submitted',
            message=f'{lead.first_name} {lead.last_name} has submitted a new application for {program_name or "a program"}.',
            link='/applications/'
        )

        return JsonResponse({'success': True, 'lead_id': lead.lead_id})

    departments = Department.objects.prefetch_related('programs').order_by('name')
    department_programs = [
        {
            'department': department,
            'programs': department.programs.all().order_by('name'),
        }
        for department in departments
        if department.programs.exists()
    ]

    current_year = date.today().year
    intake_year_choices = [current_year + offset for offset in range(4)]

    counselor_choices = Staff.objects.filter(role='counselor').order_by('full_name')
    if not counselor_choices.exists():
        counselor_choices = Staff.objects.all().order_by('full_name')

    return render(request, 'core/lead_form.html', {
        'department_programs': department_programs,
        'intake_year_choices': intake_year_choices,
        'status_choices': Lead.STATUS_CHOICES,
        'source_choices': Lead.SOURCE_CHOICES,
        'gender_choices': Lead.GENDER_CHOICES,
        'intake_semester_choices': Lead.INTAKE_SEMESTER_CHOICES,
        'education_level_choices': Lead.EDUCATION_LEVEL_CHOICES,
        'scholarship_choices': Lead.SCHOLARSHIP_INTEREST_CHOICES,
        'study_mode_choices': Lead.STUDY_MODE_CHOICES,
        'counselor_choices': counselor_choices,
    })


@login_required(login_url='login')
def applications(request):
    now = timezone.now()
    three_days_ago = now - timedelta(days=3)

    Application.objects.filter(
        status='accepted',
        approved_at__lt=three_days_ago
    ).update(status='reviewed')

    pending_applications = Application.objects.select_related('lead', 'program').filter(status='pending').order_by('-app_date')
    approved_applications = Application.objects.select_related('lead', 'program').filter(status='accepted', approved_at__gte=three_days_ago).order_by('-approved_at')
    rejected_applications = Application.objects.select_related('lead', 'program').filter(status='rejected').order_by('-rejected_at')

    pending_count = pending_applications.count()
    approved_count = approved_applications.count()
    rejected_count = rejected_applications.count()

    pending_rows = []
    for app in pending_applications:
        lead = app.lead
        pending_rows.append({
            'id': app.app_id,
            'lead_id': lead.lead_id,
            'program_id': app.program.prog_id,
            'applicant': f"{lead.first_name} {lead.last_name}",
            'email': lead.email or '—',
            'phone': lead.phone or '—',
            'program': app.program.name,
            'status': app.get_status_display(),
            'status_key': app.status,
            'submitted': app.app_date.strftime('%Y-%m-%d %H:%M'),
            'date_of_birth': lead.date_of_birth.strftime('%Y-%m-%d') if lead.date_of_birth else '',
            'gender': lead.get_gender_display() if lead.gender else '',
            'address': lead.address or '',
            'nationality': lead.nationality or '',
            'alternate_contact': lead.alternate_contact or '',
            'desired_intake_year': lead.desired_intake_year or '',
            'intake_semester': lead.get_intake_semester_display() if lead.intake_semester else '',
            'highest_education_level': lead.get_highest_education_level_display() if lead.highest_education_level else '',
            'gpa_or_percentage': lead.gpa_or_percentage or '',
            'previous_institution': lead.previous_institution or '',
            'scholarship_interest': lead.get_scholarship_interest_display() if lead.scholarship_interest else '',
            'preferred_study_mode': lead.get_preferred_study_mode_display() if lead.preferred_study_mode else '',
            'source': lead.get_source_display() if lead.source else '',
            'lead_status': lead.get_current_status_display(),
            'assigned_counselor': lead.assigned_staff.full_name if lead.assigned_staff else '',
            'followup_date': lead.followup_date.strftime('%Y-%m-%d') if lead.followup_date else '',
            'notes': lead.notes or '',
        })

    approved_rows = []
    for app in approved_applications:
        lead = app.lead
        approved_rows.append({
            'id': app.app_id,
            'lead_id': lead.lead_id,
            'applicant': f"{lead.first_name} {lead.last_name}",
            'email': lead.email or '—',
            'phone': lead.phone or '—',
            'program': app.program.name,
            'status': app.get_status_display(),
            'approved_at': app.approved_at.strftime('%Y-%m-%d %H:%M') if app.approved_at else '',
            'remaining_days': max(0, 3 - (now - app.approved_at).days) if app.approved_at else 0,
        })

    rejected_rows = []
    for app in rejected_applications:
        lead = app.lead
        rejected_rows.append({
            'id': app.app_id,
            'lead_id': lead.lead_id,
            'applicant': f"{lead.first_name} {lead.last_name}",
            'email': lead.email or '—',
            'phone': lead.phone or '—',
            'program': app.program.name,
            'status': app.get_status_display(),
            'rejected_at': app.rejected_at.strftime('%Y-%m-%d %H:%M') if app.rejected_at else '',
        })

    lead_choices = Lead.objects.order_by('first_name', 'last_name')
    program_choices = Program.objects.order_by('name')

    return render(
        request,
        'core/applications.html',
        {
            'pending_rows': pending_rows,
            'approved_rows': approved_rows,
            'rejected_rows': rejected_rows,
            'pending_count': pending_count,
            'approved_count': approved_count,
            'rejected_count': rejected_count,
            'status_choices': Application.STATUS_CHOICES,
            'lead_choices': lead_choices,
            'program_choices': program_choices,
            'gender_choices': Lead.GENDER_CHOICES,
            'intake_semester_choices': Lead.INTAKE_SEMESTER_CHOICES,
            'education_level_choices': Lead.EDUCATION_LEVEL_CHOICES,
            'scholarship_choices': Lead.SCHOLARSHIP_INTEREST_CHOICES,
            'study_mode_choices': Lead.STUDY_MODE_CHOICES,
            'source_choices': Lead.SOURCE_CHOICES,
            'status_choices_lead': Lead.STATUS_CHOICES,
            'counselor_choices': Staff.objects.filter(role='counselor').order_by('full_name'),
        },
    )


@login_required(login_url='login')
@require_http_methods(["GET"])
def application_detail_api(request, app_id):
    application = get_object_or_404(Application.objects.select_related('lead', 'program'), app_id=app_id)
    lead = application.lead
    return JsonResponse(
        {
            'success': True,
            'application': {
                'app_id': application.app_id,
                'lead_id': lead.lead_id,
                'lead_name': f"{lead.first_name} {lead.last_name}",
                'lead_first_name': lead.first_name,
                'lead_last_name': lead.last_name,
                'lead_email': lead.email or '',
                'lead_program_interest': lead.program_interest or '',
                'program_id': application.program.prog_id,
                'program_name': application.program.name,
                'status': application.status,
                'status_label': application.get_status_display(),
                'documents_url': application.documents_url or '',
                'submitted': application.app_date.strftime('%Y-%m-%d %H:%M'),
                'lead_status': lead.current_status,
                'lead_status_label': lead.get_current_status_display(),
            },
        }
    )


@login_required(login_url='login')
@require_http_methods(["POST"])
def application_create_api(request):
    lead_id = (request.POST.get('lead_id') or '').strip()
    program_id = (request.POST.get('program_id') or '').strip()
    status_value = (request.POST.get('status') or 'pending').strip()
    documents_url = (request.POST.get('documents_url') or '').strip()

    if not lead_id or not program_id:
        return JsonResponse({'success': False, 'error': 'Lead and program are required.'}, status=400)

    lead = Lead.objects.filter(lead_id=lead_id).first()
    program = Program.objects.filter(prog_id=program_id).first()

    if not lead or not program:
        return JsonResponse({'success': False, 'error': 'Invalid lead or program selected.'}, status=400)

    if status_value not in dict(Application.STATUS_CHOICES):
        return JsonResponse({'success': False, 'error': 'Invalid status selected.'}, status=400)

    application = Application.objects.create(
        lead=lead,
        program=program,
        status=status_value,
        documents_url=documents_url or None,
    )

    return JsonResponse(
        {
            'success': True,
            'application': _serialize_application_row(application),
        }
    )


@login_required(login_url='login')
@require_http_methods(["POST"])
def application_update_api(request, app_id):
    application = get_object_or_404(Application, app_id=app_id)

    lead_id = (request.POST.get('lead_id') or '').strip()
    program_id = (request.POST.get('program_id') or '').strip()
    status_value = (request.POST.get('status') or '').strip()
    documents_url = (request.POST.get('documents_url') or '').strip()
    lead_first_name = (request.POST.get('lead_first_name') or '').strip()
    lead_last_name = (request.POST.get('lead_last_name') or '').strip()
    lead_email = (request.POST.get('lead_email') or '').strip()
    lead_program_interest = (request.POST.get('lead_program_interest') or '').strip()

    if not lead_id or not program_id:
        return JsonResponse({'success': False, 'error': 'Lead and program are required.'}, status=400)

    lead = Lead.objects.filter(lead_id=lead_id).first()
    program = Program.objects.filter(prog_id=program_id).first()

    if not lead or not program:
        return JsonResponse({'success': False, 'error': 'Invalid lead or program selected.'}, status=400)

    if status_value not in dict(Application.STATUS_CHOICES):
        return JsonResponse({'success': False, 'error': 'Invalid status selected.'}, status=400)

    if not lead_first_name or not lead_last_name:
        return JsonResponse({'success': False, 'error': 'Lead first and last name are required.'}, status=400)

    application.lead = lead
    application.program = program
    application.status = status_value
    application.documents_url = documents_url or None
    application.save()

    lead.first_name = lead_first_name
    lead.last_name = lead_last_name
    lead.email = lead_email or None
    lead.program_interest = lead_program_interest or None
    lead.save()

    return JsonResponse(
        {
            'success': True,
            'application': _serialize_application_row(application),
        }
    )


@login_required(login_url='login')
@require_http_methods(["POST"])
def application_delete_api(request, app_id):
    application = get_object_or_404(Application, app_id=app_id)
    application.delete()
    return JsonResponse({'success': True})


@login_required(login_url='login')
@require_http_methods(["POST"])
def application_action_api(request, app_id):
    application = get_object_or_404(Application.objects.select_related('lead', 'program'), app_id=app_id)
    action = (request.POST.get('action') or '').strip().lower()

    action_map = {
        'review': {'app_status': 'reviewed', 'lead_status': 'qualified'},
        'accept': {'app_status': 'accepted', 'lead_status': 'converted'},
        'reject': {'app_status': 'rejected', 'lead_status': 'dropped'},
    }

    if action not in action_map:
        return JsonResponse({'success': False, 'error': 'Unsupported action.'}, status=400)

    target = action_map[action]
    application.status = target['app_status']
    
    if action == 'accept':
        application.approved_at = timezone.now()
    elif action == 'reject':
        application.rejected_at = timezone.now()
    
    application.save()

    lead = application.lead
    lead.current_status = target['lead_status']
    lead.save(update_fields=['current_status'])

    return JsonResponse(
        {
            'success': True,
            'application': _serialize_application_row(application),
            'message': f"Application marked as {application.get_status_display()} and lead updated to {lead.get_current_status_display()}.",
        }
    )


@login_required(login_url='login')
@require_http_methods(["POST"])
def application_approve_api(request, app_id):
    application = get_object_or_404(Application.objects.select_related('lead', 'program'), app_id=app_id)
    
    if application.status != 'pending':
        return JsonResponse({'success': False, 'error': 'Only pending applications can be approved.'}, status=400)

    application.status = 'accepted'
    application.approved_at = timezone.now()
    application.save(update_fields=['status', 'approved_at'])

    lead = application.lead
    lead.current_status = 'qualified'
    lead.save(update_fields=['current_status'])

    return JsonResponse({
        'success': True,
        'message': 'Application approved successfully.',
        'application': {
            'id': application.app_id,
            'status': application.get_status_display(),
            'approved_at': application.approved_at.strftime('%Y-%m-%d %H:%M'),
        }
    })


@login_required(login_url='login')
@require_http_methods(["POST"])
def application_reject_api(request, app_id):
    application = get_object_or_404(Application.objects.select_related('lead', 'program'), app_id=app_id)
    
    if application.status != 'pending':
        return JsonResponse({'success': False, 'error': 'Only pending applications can be rejected.'}, status=400)

    application.status = 'rejected'
    application.rejected_at = timezone.now()
    application.save(update_fields=['status', 'rejected_at'])

    lead = application.lead
    lead.current_status = 'dropped'
    lead.save(update_fields=['current_status'])

    return JsonResponse({
        'success': True,
        'message': 'Application rejected.',
        'application': {
            'id': application.app_id,
            'status': application.get_status_display(),
            'rejected_at': application.rejected_at.strftime('%Y-%m-%d %H:%M'),
        }
    })


@login_required(login_url='login')
@require_http_methods(["POST"])
def application_restore_api(request, app_id):
    application = get_object_or_404(Application.objects.select_related('lead', 'program'), app_id=app_id)
    
    if application.status != 'rejected':
        return JsonResponse({'success': False, 'error': 'Only rejected applications can be restored.'}, status=400)

    application.status = 'pending'
    application.rejected_at = None
    application.save(update_fields=['status', 'rejected_at'])

    lead = application.lead
    lead.current_status = 'new'
    lead.save(update_fields=['current_status'])

    return JsonResponse({
        'success': True,
        'message': 'Application restored to pending.',
        'application': {
            'id': application.app_id,
            'status': application.get_status_display(),
        }
    })


@login_required(login_url='login')
@require_http_methods(["POST"])
def application_permanent_delete_api(request, app_id):
    application = get_object_or_404(Application, app_id=app_id)
    lead_id = application.lead.lead_id
    application.delete()
    
    Lead.objects.filter(lead_id=lead_id).delete()
    
    return JsonResponse({
        'success': True,
        'message': 'Application and lead permanently deleted.',
    })


@login_required(login_url='login')
def exams(request):
    from django.utils import timezone
    now = timezone.now()

    # 1. Upcoming Sessions
    upcoming_count = EntranceExam.objects.filter(exam_date__gt=now).count()

    # 2. Registered Students (all applications with an entrance exam)
    registered_count = EntranceExam.objects.count()

    # 3. Pass Rate (calculating from those who have a result)
    total_results = EntranceExam.objects.exclude(result_status='').count()
    passed_results = EntranceExam.objects.filter(result_status='pass').count()
    pass_rate = round((passed_results / total_results) * 100) if total_results > 0 else 0

    # 4. Upcoming Exam Sessions list (approximated by listing upcoming exams or recent ones)
    exam_sessions = EntranceExam.objects.select_related('application__program', 'application__lead').order_by('-exam_date')[:10]
    
    context = {
        'upcoming_count': upcoming_count,
        'registered_count': registered_count,
        'pass_rate': pass_rate,
        'exam_sessions': exam_sessions,
    }
    return render(request, 'core/exams.html', context)


@login_required(login_url='login')
def finance(request):
    # Total Revenue (sum of verified payments)
    total_revenue = Payment.objects.filter(status='verified').aggregate(
        total=Coalesce(
            Sum('amount'),
            Value(0),
            output_field=DecimalField(max_digits=10, decimal_places=2),
        )
    )['total']

    # Pending Fees (sum of pending payments)
    pending_fees = Payment.objects.filter(status='pending').aggregate(
        total=Coalesce(
            Sum('amount'),
            Value(0),
            output_field=DecimalField(max_digits=10, decimal_places=2),
        )
    )['total']
    
    pending_count = Payment.objects.filter(status='pending').count()

    # Scholarships (Approved)
    approved_scholarships = Scholarship.objects.filter(is_approved=True).count()
    
    # Example estimation of scholarship value if percentage_off maps to a value, 
    # but we only have count here. We'll pass the count for now.

    # Recent payments for table
    recent_payments = Payment.objects.select_related('lead', 'application__program').order_by('-payment_date')[:10]

    context = {
        'total_revenue': total_revenue,
        'pending_fees': pending_fees,
        'pending_count': pending_count,
        'approved_scholarships': approved_scholarships,
        'recent_payments': recent_payments,
    }
    return render(request, 'core/finance.html', context)


@login_required(login_url='login')
def courses(request):
    departments = Department.objects.all().order_by('name')
    programs = Program.objects.select_related('dept').all().order_by('name')
    
    context = {
        'departments': departments,
        'programs': programs,
    }
    return render(request, 'core/courses.html', context)


@login_required(login_url='login')
@require_http_methods(["POST"])
def department_add_api(request):
    name = request.POST.get('name', '').strip()
    location = request.POST.get('location', '').strip()
    phone = request.POST.get('phone', '').strip()
    
    if not name:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Department name is required'})
        messages.error(request, 'Department name is required')
        return redirect('courses')
    
    dept = Department.objects.create(name=name, location=location, phone=phone)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'department': {'id': dept.dept_id, 'name': dept.name, 'location': dept.location, 'phone': dept.phone}
        })
    
    messages.success(request, 'Department added successfully')
    return redirect('courses')


@login_required(login_url='login')
@require_http_methods(["POST"])
def department_update_api(request, dept_id):
    try:
        dept = Department.objects.get(pk=dept_id)
    except Department.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Department not found'})
        messages.error(request, 'Department not found')
        return redirect('courses')
    
    name = request.POST.get('name', '').strip()
    location = request.POST.get('location', '').strip()
    phone = request.POST.get('phone', '').strip()
    
    if not name:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Department name is required'})
        messages.error(request, 'Department name is required')
        return redirect('courses')
    
    dept.name = name
    dept.location = location
    dept.phone = phone
    dept.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'department': {'id': dept.dept_id, 'name': dept.name, 'location': dept.location, 'phone': dept.phone}})
    
    messages.success(request, 'Department updated successfully')
    return redirect('courses')


@login_required(login_url='login')
@require_http_methods(["POST"])
def department_delete_api(request, dept_id):
    try:
        dept = Department.objects.get(pk=dept_id)
    except Department.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Department not found'})
        messages.error(request, 'Department not found')
        return redirect('courses')
    
    if dept.programs.exists():
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Cannot delete department with existing programs'})
        messages.error(request, 'Cannot delete department with existing programs')
        return redirect('courses')
    
    dept.delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    messages.success(request, 'Department deleted successfully')
    return redirect('courses')


@login_required(login_url='login')
@require_http_methods(["POST"])
def program_add_api(request):
    name = request.POST.get('name', '').strip()
    dept_id = request.POST.get('department')
    duration_years = request.POST.get('duration_years')
    total_fee = request.POST.get('total_fee')
    
    if not name:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Program name is required'})
        messages.error(request, 'Program name is required')
        return redirect('courses')
    if not dept_id:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Department is required'})
        messages.error(request, 'Please select a department')
        return redirect('courses')
    
    try:
        dept = Department.objects.get(pk=dept_id)
    except Department.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Department not found'})
        messages.error(request, 'Department not found')
        return redirect('courses')
    
    program = Program.objects.create(
        name=name,
        dept=dept,
        duration_years=duration_years or 4,
        total_fee=total_fee or 0
    )
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'program': {
                'id': program.prog_id,
                'name': program.name,
                'department': program.dept.name,
                'department_id': program.dept.dept_id,
                'duration_years': program.duration_years,
                'total_fee': str(program.total_fee)
            }
        })
    
    messages.success(request, 'Program added successfully')
    return redirect('courses')


@login_required(login_url='login')
@require_http_methods(["POST"])
def program_update_api(request, prog_id):
    try:
        program = Program.objects.get(pk=prog_id)
    except Program.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Program not found'})
        messages.error(request, 'Program not found')
        return redirect('courses')
    
    name = request.POST.get('name', '').strip()
    dept_id = request.POST.get('department')
    duration_years = request.POST.get('duration_years')
    total_fee = request.POST.get('total_fee')
    
    if not name:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Program name is required'})
        messages.error(request, 'Program name is required')
        return redirect('courses')
    
    if dept_id:
        try:
            dept = Department.objects.get(pk=dept_id)
            program.dept = dept
        except Department.DoesNotExist:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Department not found'})
            messages.error(request, 'Department not found')
            return redirect('courses')
    
    program.name = name
    program.duration_years = duration_years or 4
    program.total_fee = total_fee or 0
    program.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'program': {
                'id': program.prog_id,
                'name': program.name,
                'department': program.dept.name,
                'department_id': program.dept.dept_id,
                'duration_years': program.duration_years,
                'total_fee': str(program.total_fee)
            }
        })
    
    messages.success(request, 'Program updated successfully')
    return redirect('courses')


@login_required(login_url='login')
@require_http_methods(["POST"])
def program_delete_api(request, prog_id):
    try:
        program = Program.objects.get(pk=prog_id)
    except Program.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Program not found'})
        messages.error(request, 'Program not found')
        return redirect('courses')
    
    program.delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    messages.success(request, 'Program deleted successfully')
    return redirect('courses')


@login_required(login_url='login')
def profile(request):
    user = request.user
    old_email = user.email
    staff_profile = Staff.objects.filter(Q(email=user.email) | Q(email=old_email)).first()

    if request.method == 'POST':
        # Handle staff profile update
        if 'full_name' in request.POST or 'phone' in request.POST or 'bio' in request.POST or 'department' in request.POST:
            if staff_profile:
                staff_profile.full_name = request.POST.get('full_name', staff_profile.full_name)
                staff_profile.phone = request.POST.get('phone', '') or None
                staff_profile.bio = request.POST.get('bio', '') or None
                staff_profile.department = request.POST.get('department', '') or None
                staff_profile.save(update_fields=['full_name', 'phone', 'bio', 'department'])
                messages.success(request, 'Profile information updated successfully.')
                return redirect('profile')

        messages.error(request, 'Please correct the errors below and try again.')

    context = {
        'staff': staff_profile,
    }
    return render(request, 'core/profile.html', context)


@login_required(login_url='login')
def settings(request):
    staff_profile = Staff.objects.filter(email=request.user.email).first()
    context = {
        'staff': staff_profile,
    }
    return render(request, 'core/settings.html', context)


def home(request):
    return render(request, 'core/homepage.html')


@login_required(login_url='login')
@require_http_methods(["GET"])
def notifications_api(request):
    notifications = Notification.objects.all()[:20]
    unread_count = Notification.objects.filter(is_read=False).count()
    
    data = []
    for notif in notifications:
        data.append({
            'id': notif.notification_id,
            'type': notif.notification_type,
            'title': notif.title,
            'message': notif.message,
            'link': notif.link,
            'is_read': notif.is_read,
            'created_at': notif.created_at.strftime('%Y-%m-%d %H:%M'),
        })
    
    return JsonResponse({
        'success': True,
        'notifications': data,
        'unread_count': unread_count,
    })


@login_required(login_url='login')
@require_http_methods(["POST"])
def mark_notification_read_api(request, notif_id):
    notif = get_object_or_404(Notification, notification_id=notif_id)
    notif.is_read = True
    notif.save(update_fields=['is_read'])
    
    return JsonResponse({'success': True})


@login_required(login_url='login')
@require_http_methods(["POST"])
def mark_all_notifications_read_api(request):
    Notification.objects.filter(is_read=False).update(is_read=True)
    
    return JsonResponse({'success': True})
