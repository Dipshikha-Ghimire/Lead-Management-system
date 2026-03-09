from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from django.db.models import Sum, Count, DecimalField, Value
from django.db.models.functions import Coalesce
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from .forms import LoginForm, SignupForm
from .models import Lead, Program, Application, EntranceExam, Scholarship, Payment, Staff


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
    total_leads = Lead.objects.count()
    qualified_leads = Lead.objects.filter(current_status='qualified').count()
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

    pending_applications = Application.objects.filter(status='pending').count()
    pending_scholarships = Scholarship.objects.filter(is_approved=False).count()

    source_totals = Lead.objects.values('source').annotate(count=Count('lead_id')).order_by('source')
    source_totals = [
        {
            'label': item['source'].replace('_', ' ').title(),
            'count': item['count'],
            'percent': round((item['count'] / total_leads) * 100) if total_leads else 0,
        }
        for item in source_totals
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
        'qualified_leads': qualified_leads,
        'enrolled_count': accepted_applications,
        'verified_revenue': verified_revenue,
        'pending_applications': pending_applications,
        'pending_scholarships': pending_scholarships,
        'funnel_capture': total_leads,
        'funnel_qualification': qualified_leads,
        'funnel_review': reviewed_applications,
        'funnel_exam': exam_count,
        'funnel_enrolled': accepted_applications,
        'source_totals': source_totals,
        'recent_leads': recent_leads,
    }

    return render(request, 'core/dashboard.html', context)


@login_required(login_url='login')
def leads(request):
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    leads_qs = Lead.objects.prefetch_related('applications__program').order_by('-created_at')

    if query:
        leads_qs = leads_qs.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
            | Q(current_status__icontains=query)
            | Q(source__icontains=query)
            | Q(applications__program__name__icontains=query)
        ).distinct()

    if status_filter:
        leads_qs = leads_qs.filter(current_status=status_filter)

    lead_rows = []
    for lead in leads_qs:
        applications = list(lead.applications.all())
        latest_application = max(applications, key=lambda item: item.app_date) if applications else None
        lead_rows.append(
            {
                'id': lead.lead_id,
                'name': f"{lead.first_name} {lead.last_name}",
                'email': lead.email or '—',
                'program': latest_application.program.name if latest_application else '—',
                'status': lead.get_current_status_display(),
                'status_key': lead.current_status,
                'updated': lead.created_at,
            }
        )

    status_choices = Lead.STATUS_CHOICES

    return render(request, 'core/leads.html', {
        'lead_rows': lead_rows,
        'query': query,
        'status_filter': status_filter,
        'status_choices': status_choices,
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
            'source': lead.source,
            'source_label': lead.get_source_display(),
            'current_status': lead.current_status,
            'current_status_label': lead.get_current_status_display(),
            'program_interest': lead.program_interest or '',
            'notes': lead.notes or '',
            'created_at': lead.created_at.strftime('%Y-%m-%d %H:%M'),
        },
    })


@login_required(login_url='login')
@require_http_methods(["POST"])
def lead_update_api(request, lead_id):
    lead = get_object_or_404(Lead, lead_id=lead_id)

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

    lead.first_name = first_name
    lead.last_name = last_name
    lead.email = (request.POST.get('email') or '').strip() or None
    lead.phone = (request.POST.get('phone') or '').strip() or None
    lead.program_interest = (request.POST.get('program_interest') or '').strip() or None
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
            'status': lead.get_current_status_display(),
            'status_key': lead.current_status,
            'program_interest': lead.program_interest or '—',
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

        return JsonResponse({'success': True, 'lead_id': lead.lead_id})

    return render(request, 'core/lead_form.html', {
        'status_choices': Lead.STATUS_CHOICES,
    })


@login_required(login_url='login')
def applications(request):
    query = (request.GET.get('q') or '').strip()
    status_filter = (request.GET.get('status') or '').strip()

    applications_qs = Application.objects.select_related('lead', 'program').order_by('-app_date')

    if query:
        applications_qs = applications_qs.filter(
            Q(lead__first_name__icontains=query)
            | Q(lead__last_name__icontains=query)
            | Q(lead__email__icontains=query)
            | Q(program__name__icontains=query)
            | Q(status__icontains=query)
        )

    if status_filter:
        applications_qs = applications_qs.filter(status=status_filter)

    total_submitted = Application.objects.count()
    reviewed_count = Application.objects.filter(status='reviewed').count()
    accepted_count = Application.objects.filter(status='accepted').count()
    rejected_count = Application.objects.filter(status='rejected').count()

    application_rows = []
    for application in applications_qs:
        row = _serialize_application_row(application)
        row['submitted'] = application.app_date
        application_rows.append(row)

    lead_choices = Lead.objects.order_by('first_name', 'last_name')
    program_choices = Program.objects.order_by('name')

    return render(
        request,
        'core/applications.html',
        {
            'application_rows': application_rows,
            'total_submitted': total_submitted,
            'reviewed_count': reviewed_count,
            'accepted_count': accepted_count,
            'rejected_count': rejected_count,
            'query': query,
            'status_filter': status_filter,
            'status_choices': Application.STATUS_CHOICES,
            'lead_choices': lead_choices,
            'program_choices': program_choices,
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
    application.save(update_fields=['status'])

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
def exams(request):
    return render(request, 'core/exams.html')


@login_required(login_url='login')
def finance(request):
    return render(request, 'core/finance.html')


@login_required(login_url='login')
def settings(request):
    return render(request, 'core/settings.html')


def home(request):
    return render(request, 'core/homepage.html')
