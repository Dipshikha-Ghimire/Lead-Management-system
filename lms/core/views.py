from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.messages import get_messages
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.db import transaction, IntegrityError
from django.db.models import Sum, Count, DecimalField, Value
from django.db.models.functions import Coalesce
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from .forms import LoginForm, SignupForm, LeadSubmissionForm
from .models import Lead, Program, Application, EntranceExam, Scholarship, Payment, Staff, Admin, Department, Notification


def get_user_role(user):
    if user.is_superuser:
        return 'admin'
    if user.groups.filter(name='admin').exists():
        return 'admin'
    if user.groups.filter(name='staff').exists():
        return 'staff'
    if user.groups.filter(name='lead').exists():
        return 'lead'
    return None


def get_staff_department(user):
    if not user.is_authenticated:
        return None
    staff = Staff.objects.filter(user=user).first()
    if staff and staff.department:
        return staff.department
    return None


def get_staff_department_programs(user):
    dept = get_staff_department(user)
    if dept:
        return Program.objects.filter(dept=dept)
    return Program.objects.none()


def get_accessible_applications_qs(user):
    user_role = get_user_role(user)
    if user_role == 'staff':
        dept = get_staff_department(user)
        if not dept:
            return Application.objects.none()
        return Application.objects.filter(program__dept=dept)
    return Application.objects.all()


def get_accessible_leads_qs(user):
    user_role = get_user_role(user)
    if user_role == 'staff':
        dept = get_staff_department(user)
        if not dept:
            return Lead.objects.none()
        return Lead.objects.filter(applications__program__dept=dept).distinct()
    return Lead.objects.all()


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


def _first_form_error(form):
    for field_errors in form.errors.values():
        if field_errors:
            return field_errors[0]
    return 'Please correct the highlighted fields and try again.'


# ---------- AUTH VIEWS ----------

def login_view(request):
    if request.user.is_authenticated:
        user_role = get_user_role(request.user)
        if user_role == 'lead':
            return redirect('lead_dashboard')
        return redirect('dashboard')
    
    next_url = request.POST.get('next') or request.GET.get('next')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.user
            login(request, user)

            remember_me = form.cleaned_data.get('remember_me', False)
            if not remember_me:
                request.session.set_expiry(0)
            
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            
            user_role = get_user_role(user)
            if user_role == 'lead':
                return redirect('lead_dashboard')
            return redirect('dashboard')
    else:
        form = LoginForm()
        next_url = request.GET.get('next')
    
    return render(request, 'core/login.html', {'form': form, 'next': next_url})


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password1']
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            
            lead_group, _ = Group.objects.get_or_create(name='lead')
            user.groups.add(lead_group)
            
            messages.success(request, 'Account created successfully! Please login with your credentials.')
            return redirect('login')
    else:
        form = SignupForm()
    
    return render(request, 'core/signup.html', {'form': form})


def staff_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        user_role = get_user_role(request.user)
        if user_role not in ['admin', 'staff']:
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def logout_view(request):
    # Drain queued flash messages so stale messages do not show after logout/login cycles.
    for _ in get_messages(request):
        pass

    logout(request)

    # Ensure no messages remain in storage for the next anonymous request.
    for _ in get_messages(request):
        pass

    return redirect('login')


def is_staff_user(user):
    if not user.is_authenticated:
        return False
    return get_user_role(user) == 'staff'


def is_admin_user(user):
    if not user.is_authenticated:
        return False
    return get_user_role(user) == 'admin'


# ---------- STAFF DASHBOARD ----------
@login_required(login_url='login')
def staff_dashboard(request):
    user_role = get_user_role(request.user)
    if user_role not in ['admin', 'staff']:
        return redirect('dashboard')
    
    user_dept = get_staff_department(request.user)
    
    if user_dept:
        dept_programs = Program.objects.filter(dept=user_dept)
        dept_program_ids = dept_programs.values_list('prog_id', flat=True)
        
        recent_leads_qs = Lead.objects.filter(
            applications__program__in=dept_program_ids
        ).prefetch_related('applications__program').order_by('-created_at')[:5]
    else:
        recent_leads_qs = Lead.objects.none()
    
    recent_leads = []
    for lead in recent_leads_qs:
        latest_application = lead.applications.select_related('program').order_by('-app_date').first()
        recent_leads.append({
            'name': f"{lead.first_name} {lead.last_name}",
            'program': latest_application.program.name if latest_application else '—',
            'stage': lead.get_current_status_display(),
            'date': lead.created_at,
        })
    
    context = {
        'staff_department': user_dept.name if user_dept else None,
        'recent_leads': recent_leads,
    }
    return render(request, 'core/staff_dashboard.html', context)


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
    
    user_role = get_user_role(request.user)
    user_dept = get_staff_department(request.user)
    
    if user_role == 'staff' and user_dept:
        dept_programs = Program.objects.filter(dept=user_dept)
        dept_program_ids = dept_programs.values_list('prog_id', flat=True)
        leads_qs = Lead.objects.filter(
            applications__program__in=dept_program_ids
        ).prefetch_related('applications__program').distinct().order_by('-created_at')
    else:
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

        enrollment_note = ''
        if approved_app and approved_app.exam_score is not None:
            score = float(approved_app.exam_score)
            is_failed = (approved_app.exam_result == 'fail') or (score < 40)
            if is_failed:
                enrollment_note = 'Dropped due to exam result below pass mark.'
            elif approved_app.scholarship_approved:
                if approved_app.scholarship_percentage:
                    enrollment_note = f"Scholarship approved: {approved_app.scholarship_percentage}%"
                else:
                    enrollment_note = 'Scholarship approved.'
            else:
                enrollment_note = 'No Scholarship'
        
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
                'highest_education_level': lead.get_highest_education_level_display() if lead.highest_education_level else '',
                'gpa_or_percentage': lead.gpa_or_percentage or '',
                'previous_institution': lead.previous_institution or '',
                'education_document': lead.education_document.url if lead.education_document else '',
                'scholarship_interest': lead.get_scholarship_interest_display() if lead.scholarship_interest else '',
                'preferred_study_mode': lead.get_preferred_study_mode_display() if lead.preferred_study_mode else '',
                'source': lead.get_source_display() if lead.source else '',
                'lead_status': lead.get_current_status_display(),
                'assigned_counselor': lead.assigned_staff.full_name if lead.assigned_staff else '',
                'followup_date': lead.followup_date.strftime('%Y-%m-%d') if lead.followup_date else '',
                'notes': lead.notes or '',
                'exam_score': approved_app.exam_score if approved_app and approved_app.exam_score is not None else '',
                'exam_result': approved_app.get_exam_result_display() if approved_app and approved_app.exam_result else '',
                'scholarship_percentage': approved_app.scholarship_percentage if approved_app and approved_app.scholarship_percentage is not None else '',
                'scholarship_approved': approved_app.scholarship_approved if approved_app else False,
                'final_course_fee': approved_app.final_course_fee if approved_app and approved_app.final_course_fee is not None else '',
                'enrollment_note': enrollment_note,
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
        'education_level_choices': Lead.EDUCATION_LEVEL_CHOICES,
        'scholarship_choices': Lead.SCHOLARSHIP_INTEREST_CHOICES,
        'study_mode_choices': Lead.STUDY_MODE_CHOICES,
        'counselor_choices': counselor_choices,
        'intake_year_choices': intake_year_choices,
        'program_choices': program_choices,
        'is_staff_user': user_role == 'staff',
        'is_admin_user': user_role == 'admin',
    })


@login_required(login_url='login')
@require_http_methods(["GET"])
def lead_detail_api(request, lead_id):
    lead = get_object_or_404(Lead, lead_id=lead_id)
    
    # Get the latest application to fetch exam/scholarship data
    latest_app = lead.applications.select_related('program').order_by('-app_date').first()
    
    # Compute enrollment note based on exam result and scholarship status
    enrollment_note = ''
    exam_score = ''
    exam_result = ''
    scholarship_percentage = ''
    scholarship_approved = False
    final_course_fee = ''
    
    if latest_app:
        if latest_app.exam_score is not None:
            exam_score = str(latest_app.exam_score)
            exam_result = latest_app.get_exam_result_display() if latest_app.exam_result else ''
            score = float(latest_app.exam_score)
            is_failed = (latest_app.exam_result == 'fail') or (score < 40)
            
            if is_failed:
                enrollment_note = 'Dropped due to exam result below pass mark.'
            elif latest_app.scholarship_approved:
                if latest_app.scholarship_percentage:
                    scholarship_percentage = str(latest_app.scholarship_percentage)
                    enrollment_note = f"Scholarship approved: {latest_app.scholarship_percentage}%"
                else:
                    enrollment_note = 'Scholarship approved.'
            else:
                enrollment_note = 'No Scholarship'
            
            scholarship_approved = latest_app.scholarship_approved
            if latest_app.final_course_fee is not None:
                final_course_fee = str(latest_app.final_course_fee)
    
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
            'highest_education_level': lead.highest_education_level or '',
            'highest_education_level_label': lead.get_highest_education_level_display() if lead.highest_education_level else '',
            'gpa_or_percentage': lead.gpa_or_percentage or '',
            'previous_institution': lead.previous_institution or '',
            'education_document': lead.education_document.url if lead.education_document else '',
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
            'exam_score': exam_score,
            'exam_result': exam_result,
            'scholarship_percentage': scholarship_percentage,
            'scholarship_approved': scholarship_approved,
            'final_course_fee': final_course_fee,
            'enrollment_note': enrollment_note,
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

    education_value = (request.POST.get('highest_education_level') or '').strip()
    if education_value and education_value not in dict(Lead.EDUCATION_LEVEL_CHOICES):
        return JsonResponse({'success': False, 'error': 'Invalid education level selected.'}, status=400)

    scholarship_value = (request.POST.get('scholarship_interest') or '').strip()
    if scholarship_value and scholarship_value not in dict(Lead.SCHOLARSHIP_INTEREST_CHOICES):
        return JsonResponse({'success': False, 'error': 'Invalid scholarship option selected.'}, status=400)

    study_mode_value = (request.POST.get('preferred_study_mode') or '').strip()
    if study_mode_value and study_mode_value not in dict(Lead.STUDY_MODE_CHOICES):
        return JsonResponse({'success': False, 'error': 'Invalid study mode selected.'}, status=400)

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
    if request.FILES.get('education_document'):
        lead.education_document = request.FILES.get('education_document')
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
            'education_level': lead.get_highest_education_level_display() if lead.highest_education_level else '—',
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
@staff_required
def lead_form(request):
    if request.method == 'POST':
        form = LeadSubmissionForm(request.POST, request.FILES, user_role='admin')
        if not form.is_valid():
            return JsonResponse({'success': False, 'error': _first_form_error(form), 'errors': form.errors}, status=400)

        cleaned = form.cleaned_data

        try:
            with transaction.atomic():
                lead = Lead.objects.create(
                    first_name=cleaned['first_name'],
                    last_name=cleaned['last_name'],
                    email=cleaned.get('email') or None,
                    phone=cleaned.get('phone') or None,
                    date_of_birth=cleaned.get('date_of_birth'),
                    gender=cleaned.get('gender') or None,
                    address=cleaned.get('address') or None,
                    nationality=cleaned.get('nationality') or None,
                    alternate_contact=cleaned.get('alternate_contact') or None,
                    program_interest=cleaned['program_interest'],
                    highest_education_level=cleaned['education_level'],
                    gpa_or_percentage=cleaned.get('gpa_or_percentage') or None,
                    previous_institution=cleaned.get('previous_institution') or None,
                    education_document=cleaned.get('education_document'),
                    scholarship_interest=cleaned.get('scholarship_interest') or None,
                    preferred_study_mode=cleaned.get('study_mode') or None,
                    source=cleaned['lead_source'],
                    current_status=cleaned.get('lead_status') or 'new',
                    followup_date=cleaned.get('followup_date'),
                    notes=cleaned.get('notes') or None,
                    assigned_staff=cleaned.get('counselor'),
                )

                Application.objects.create(
                    lead=lead,
                    program=cleaned['program_obj'],
                    status='pending'
                )

                Notification.objects.create(
                    notification_type='new_application',
                    title='New Application Submitted',
                    message=f"{lead.first_name} {lead.last_name} has submitted a new application for {cleaned['program_interest']}.",
                    link='/applications/'
                )
        except IntegrityError:
            return JsonResponse({'success': False, 'error': 'Unable to save application right now.'}, status=500)

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
        'status_choices': Lead.STATUS_CHOICES,
        'source_choices': Lead.SOURCE_CHOICES,
        'gender_choices': Lead.GENDER_CHOICES,
        'education_level_choices': Lead.EDUCATION_LEVEL_CHOICES,
        'scholarship_choices': Lead.SCHOLARSHIP_INTEREST_CHOICES,
        'study_mode_choices': Lead.STUDY_MODE_CHOICES,
        'counselor_choices': counselor_choices,
    })


@login_required(login_url='login')
def applications(request):
    now = timezone.now()
    three_days_ago = now - timedelta(days=3)

    accessible_applications = get_accessible_applications_qs(request.user)

    accessible_applications.filter(
        status='accepted',
        approved_at__lt=three_days_ago
    ).update(status='reviewed')

    scoped_applications = accessible_applications.select_related('lead', 'program')

    pending_applications = scoped_applications.filter(status='pending').order_by('-app_date')
    approved_applications = scoped_applications.filter(status='accepted', approved_at__gte=three_days_ago).order_by('-approved_at')
    rejected_applications = scoped_applications.filter(status='rejected').order_by('-rejected_at')

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
            'highest_education_level': lead.get_highest_education_level_display() if lead.highest_education_level else '',
            'gpa_or_percentage': lead.gpa_or_percentage or '',
            'previous_institution': lead.previous_institution or '',
            'education_document': lead.education_document.url if lead.education_document else '',
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
            'status_key': app.status,
            'submitted': app.app_date.strftime('%Y-%m-%d %H:%M'),
            'approved_at': app.approved_at.strftime('%Y-%m-%d %H:%M') if app.approved_at else '',
            'remaining_days': max(0, 3 - (now - app.approved_at).days) if app.approved_at else 0,
            'date_of_birth': lead.date_of_birth.strftime('%Y-%m-%d') if lead.date_of_birth else '',
            'gender': lead.get_gender_display() if lead.gender else '',
            'address': lead.address or '',
            'nationality': lead.nationality or '',
            'alternate_contact': lead.alternate_contact or '',
            'highest_education_level': lead.get_highest_education_level_display() if lead.highest_education_level else '',
            'gpa_or_percentage': lead.gpa_or_percentage or '',
            'previous_institution': lead.previous_institution or '',
            'education_document': lead.education_document.url if lead.education_document else '',
            'scholarship_interest': lead.get_scholarship_interest_display() if lead.scholarship_interest else '',
            'preferred_study_mode': lead.get_preferred_study_mode_display() if lead.preferred_study_mode else '',
            'source': lead.get_source_display() if lead.source else '',
            'lead_status': lead.get_current_status_display(),
            'assigned_counselor': lead.assigned_staff.full_name if lead.assigned_staff else '',
            'followup_date': lead.followup_date.strftime('%Y-%m-%d') if lead.followup_date else '',
            'notes': lead.notes or '',
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
            'status_key': app.status,
            'submitted': app.app_date.strftime('%Y-%m-%d %H:%M'),
            'rejected_at': app.rejected_at.strftime('%Y-%m-%d %H:%M') if app.rejected_at else '',
            'date_of_birth': lead.date_of_birth.strftime('%Y-%m-%d') if lead.date_of_birth else '',
            'gender': lead.get_gender_display() if lead.gender else '',
            'address': lead.address or '',
            'nationality': lead.nationality or '',
            'alternate_contact': lead.alternate_contact or '',
            'highest_education_level': lead.get_highest_education_level_display() if lead.highest_education_level else '',
            'gpa_or_percentage': lead.gpa_or_percentage or '',
            'previous_institution': lead.previous_institution or '',
            'education_document': lead.education_document.url if lead.education_document else '',
            'scholarship_interest': lead.get_scholarship_interest_display() if lead.scholarship_interest else '',
            'preferred_study_mode': lead.get_preferred_study_mode_display() if lead.preferred_study_mode else '',
            'source': lead.get_source_display() if lead.source else '',
            'lead_status': lead.get_current_status_display(),
            'assigned_counselor': lead.assigned_staff.full_name if lead.assigned_staff else '',
            'followup_date': lead.followup_date.strftime('%Y-%m-%d') if lead.followup_date else '',
            'notes': lead.notes or '',
        })

    lead_choices = get_accessible_leads_qs(request.user).order_by('first_name', 'last_name')
    user_role = get_user_role(request.user)
    user_dept = get_staff_department(request.user)
    if user_role == 'staff':
        if user_dept:
            program_choices = Program.objects.filter(dept=user_dept).order_by('name')
        else:
            program_choices = Program.objects.none()
    else:
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
    application = get_object_or_404(
        get_accessible_applications_qs(request.user).select_related('lead', 'program'),
        app_id=app_id,
    )
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
    program = Program.objects.select_related('dept').filter(prog_id=program_id).first()

    if not lead or not program:
        return JsonResponse({'success': False, 'error': 'Invalid lead or program selected.'}, status=400)

    user_role = get_user_role(request.user)
    if user_role == 'staff':
        user_dept = get_staff_department(request.user)
        if not user_dept or program.dept_id != user_dept.dept_id:
            return JsonResponse({'success': False, 'error': 'You can only create applications for your department.'}, status=403)

        lead_in_department = get_accessible_leads_qs(request.user).filter(lead_id=lead.lead_id).exists()
        if not lead_in_department:
            return JsonResponse({'success': False, 'error': 'You can only use leads from your department.'}, status=403)

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
    application = get_object_or_404(get_accessible_applications_qs(request.user), app_id=app_id)

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
    program = Program.objects.select_related('dept').filter(prog_id=program_id).first()

    if not lead or not program:
        return JsonResponse({'success': False, 'error': 'Invalid lead or program selected.'}, status=400)

    user_role = get_user_role(request.user)
    if user_role == 'staff':
        user_dept = get_staff_department(request.user)
        if not user_dept or program.dept_id != user_dept.dept_id:
            return JsonResponse({'success': False, 'error': 'You can only assign programs from your department.'}, status=403)

        lead_in_department = get_accessible_leads_qs(request.user).filter(lead_id=lead.lead_id).exists()
        if not lead_in_department:
            return JsonResponse({'success': False, 'error': 'You can only assign leads from your department.'}, status=403)

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
    application = get_object_or_404(get_accessible_applications_qs(request.user), app_id=app_id)
    application.delete()
    return JsonResponse({'success': True})


@login_required(login_url='login')
@require_http_methods(["POST"])
def application_action_api(request, app_id):
    application = get_object_or_404(
        get_accessible_applications_qs(request.user).select_related('lead', 'program'),
        app_id=app_id,
    )
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
    application = get_object_or_404(
        get_accessible_applications_qs(request.user).select_related('lead', 'program'),
        app_id=app_id,
    )
    
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
    application = get_object_or_404(
        get_accessible_applications_qs(request.user).select_related('lead', 'program'),
        app_id=app_id,
    )
    
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
    application = get_object_or_404(
        get_accessible_applications_qs(request.user).select_related('lead', 'program'),
        app_id=app_id,
    )
    
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
    application = get_object_or_404(get_accessible_applications_qs(request.user), app_id=app_id)
    lead_id = application.lead.lead_id
    application.delete()
    
    Lead.objects.filter(lead_id=lead_id).delete()
    
    return JsonResponse({
        'success': True,
        'message': 'Application and lead permanently deleted.',
    })


@login_required(login_url='login')
def exams(request):
    user_role = get_user_role(request.user)
    user_dept = get_staff_department(request.user)
    
    if user_role == 'staff' and user_dept:
        dept_programs = Program.objects.filter(dept=user_dept)
        dept_program_ids = dept_programs.values_list('prog_id', flat=True)
        
        entrance_exam_leads = Application.objects.filter(
            lead__current_status='exams',
            exam_score__isnull=True,
            program__in=dept_program_ids
        ).select_related('lead', 'program').order_by('-app_date')

        scholarship_leads = Application.objects.filter(
            exam_score__isnull=False,
            lead__current_status='exams',
            program__in=dept_program_ids
        ).select_related('lead', 'program').order_by('-exam_date', '-app_date')

        enrolled_leads = Application.objects.filter(
            exam_score__isnull=False,
            lead__current_status__in=['enrolled', 'dropped'],
            program__in=dept_program_ids
        ).select_related('lead', 'program').order_by('-exam_date', '-app_date')[:20]
    else:
        entrance_exam_leads = Application.objects.filter(
            lead__current_status='exams',
            exam_score__isnull=True
        ).select_related('lead', 'program').order_by('-app_date')

        scholarship_leads = Application.objects.filter(
            exam_score__isnull=False,
            lead__current_status='exams',
        ).select_related('lead', 'program').order_by('-exam_date', '-app_date')

        enrolled_leads = Application.objects.filter(
            exam_score__isnull=False,
            lead__current_status__in=['enrolled', 'dropped'],
        ).select_related('lead', 'program').order_by('-exam_date', '-app_date')[:20]

    context = {
        'entrance_exam_leads': entrance_exam_leads,
        'scholarship_leads': scholarship_leads,
        'enrolled_leads': enrolled_leads,
    }
    return render(request, 'core/exams.html', context)


@login_required(login_url='login')
@staff_required
@require_http_methods(["GET"])
def exam_detail_api(request):
    app_id = request.GET.get('application_id')
    
    if not app_id:
        return JsonResponse({'success': False, 'error': 'Application ID is required.'}, status=400)
    
    application = get_object_or_404(get_accessible_applications_qs(request.user), app_id=app_id)
    
    return JsonResponse({
        'success': True,
        'exam': {
            'application_id': application.app_id,
            'exam_name': application.exam_name or '',
            'exam_date': application.exam_date.strftime('%Y-%m-%d') if application.exam_date else '',
            'exam_type': application.exam_type or '',
            'exam_score': str(application.exam_score) if application.exam_score else '',
            'exam_result': application.exam_result or '',
        },
    })


@login_required(login_url='login')
@staff_required
@require_http_methods(["POST"])
def submit_exam_info(request):
    app_id = request.POST.get('application_id')
    exam_name = request.POST.get('exam_name')
    exam_date = request.POST.get('exam_date')
    exam_type = request.POST.get('exam_type')
    exam_score = request.POST.get('exam_score')
    
    try:
        application = get_object_or_404(get_accessible_applications_qs(request.user), app_id=app_id)
        from datetime import datetime
        exam_date_obj = datetime.strptime(exam_date, '%Y-%m-%d') if exam_date else timezone.now()
        
        application.exam_name = exam_name
        application.exam_date = exam_date_obj
        application.exam_type = exam_type
        application.exam_score = exam_score
        
        # Determine pass/fail based on score >= 40
        score = Decimal(str(exam_score or '0'))
        course_fee = application.program.total_fee or Decimal('0')
        if score >= Decimal('40'):
            application.exam_result = 'pass'
            # Auto-calculate scholarship if score > 90 (up to 40%)
            if score > Decimal('90'):
                scholarship_percentage = min(Decimal('40'), (score - Decimal('90')) * Decimal('4'))
                application.scholarship_percentage = scholarship_percentage
                application.final_course_fee = course_fee * (Decimal('1') - (scholarship_percentage / Decimal('100')))
            else:
                application.scholarship_percentage = Decimal('0')
                application.final_course_fee = course_fee
        else:
            application.exam_result = 'fail'
            application.scholarship_percentage = Decimal('0')
            application.final_course_fee = course_fee
        
        application.save()
        
        return JsonResponse({'success': True, 'message': 'Exam information submitted successfully.'})
    except (InvalidOperation, TypeError, ValueError) as e:
        return JsonResponse({'success': False, 'error': f'Invalid score value: {e}'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required(login_url='login')
@staff_required
@require_http_methods(["POST"])
def approve_scholarship(request):
    app_id = request.POST.get('application_id')
    
    try:
        application = get_object_or_404(get_accessible_applications_qs(request.user), app_id=app_id)
        score = Decimal(str(application.exam_score or '0'))
        is_failed = (application.exam_result == 'fail') or (score < Decimal('40'))
        course_fee = application.program.total_fee or Decimal('0')
        
        # Calculate scholarship if not already calculated (for scores > 90)
        if application.exam_score and score > Decimal('90') and not application.scholarship_percentage:
            scholarship_percentage = min(Decimal('40'), (score - Decimal('90')) * Decimal('4'))
            application.scholarship_percentage = scholarship_percentage
            application.final_course_fee = course_fee * (Decimal('1') - (scholarship_percentage / Decimal('100')))
        elif application.final_course_fee is None:
            application.scholarship_percentage = application.scholarship_percentage or Decimal('0')
            application.final_course_fee = course_fee
        
        application.scholarship_approved = True
        application.save()
        
        # Only failed exams (or score < 40) should move to dropped.
        if is_failed:
            application.lead.current_status = 'dropped'
        else:
            application.lead.current_status = 'enrolled'
        application.lead.save(update_fields=['current_status'])
        
        return JsonResponse({'success': True, 'message': 'Scholarship approved successfully.'})
    except (InvalidOperation, TypeError, ValueError) as e:
        return JsonResponse({'success': False, 'error': f'Invalid numeric data: {e}'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required(login_url='login')
@staff_required
@require_http_methods(["POST"])
def disapprove_scholarship(request):
    app_id = request.POST.get('application_id')
    
    try:
        application = get_object_or_404(get_accessible_applications_qs(request.user), app_id=app_id)
        score = Decimal(str(application.exam_score or '0'))
        is_failed = (application.exam_result == 'fail') or (score < Decimal('40'))
        
        # Set scholarship to 0 (explicitly no scholarship).
        application.scholarship_percentage = Decimal('0')
        application.scholarship_approved = False
        application.final_course_fee = application.program.total_fee or Decimal('0')
        application.save()
        
        # Only failed exams (or score < 40) should move to dropped.
        if is_failed:
            application.lead.current_status = 'dropped'
        else:
            application.lead.current_status = 'enrolled'
        application.lead.save(update_fields=['current_status'])
        
        return JsonResponse({'success': True, 'message': 'Scholarship disapproved.'})
    except (InvalidOperation, TypeError, ValueError) as e:
        return JsonResponse({'success': False, 'error': f'Invalid numeric data: {e}'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


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
@staff_required
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
@staff_required
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
@staff_required
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
@staff_required
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
@staff_required
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
@staff_required
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
    user_role = get_user_role(user)
    
    if user_role == 'admin' or user.is_superuser:
        admin_profile = Admin.objects.filter(Q(email=user.email) | Q(user=user)).first()
        if admin_profile or user.is_superuser:
            return redirect('admin_profile')
    
    old_email = user.email
    staff_profile = Staff.objects.filter(Q(email=user.email) | Q(email=old_email) | Q(user=user)).first()

    if request.method == 'POST':
        if 'full_name' in request.POST or 'phone' in request.POST or 'bio' in request.POST or 'department' in request.POST:
            if staff_profile:
                new_email = (request.POST.get('email') or user.email or '').strip().lower()
                if not new_email:
                    messages.error(request, 'Email address is required.')
                    return redirect('profile')

                duplicate_user = User.objects.filter(email__iexact=new_email).exclude(pk=user.pk).exists()
                duplicate_staff = Staff.objects.filter(email__iexact=new_email).exclude(pk=staff_profile.pk).exists()
                if duplicate_user or duplicate_staff:
                    messages.error(request, 'Email is already in use by another account.')
                    return redirect('profile')

                user.email = new_email
                user.save(update_fields=['email'])

                staff_profile.full_name = (request.POST.get('full_name', staff_profile.full_name) or '').strip()
                staff_profile.phone = request.POST.get('phone', '') or None
                staff_profile.bio = request.POST.get('bio', '') or None

                if user_role != 'staff':
                    department_id = request.POST.get('department', '')
                    if department_id:
                        try:
                            staff_profile.department = Department.objects.get(pk=department_id)
                        except Department.DoesNotExist:
                            staff_profile.department = None
                    else:
                        staff_profile.department = None

                staff_profile.email = new_email
                fields_to_update = ['full_name', 'phone', 'bio', 'email']
                if user_role != 'staff':
                    fields_to_update.append('department')

                staff_profile.save(update_fields=fields_to_update)
                messages.success(request, 'Profile information updated successfully.')
                return redirect('profile')

        messages.error(request, 'Please correct the errors below and try again.')

    context = {
        'staff': staff_profile,
        'departments': Department.objects.all().order_by('name'),
    }
    return render(request, 'core/profile.html', context)


@login_required(login_url='login')
def settings(request):
    staff_profile = Staff.objects.filter(email=request.user.email).first()
    context = {
        'staff': staff_profile,
    }
    return render(request, 'core/settings.html', context)


@login_required(login_url='login')
@require_http_methods(["POST"])
def change_password_api(request):
    old_password = request.POST.get('old_password', '')
    new_password1 = request.POST.get('new_password1', '')
    new_password2 = request.POST.get('new_password2', '')
    
    errors = []
    
    if not old_password:
        errors.append('Current password is required.')
    
    if not new_password1:
        errors.append('New password is required.')
    elif len(new_password1) < 8:
        errors.append('New password must be at least 8 characters.')
    
    if not new_password2:
        errors.append('Please confirm your new password.')
    elif new_password1 != new_password2:
        errors.append('New passwords do not match.')
    
    if not errors and old_password:
        user = request.user
        if not user.check_password(old_password):
            errors.append('Current password is incorrect.')
    
    if not errors and new_password1 and new_password2:
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError
        try:
            validate_password(new_password1, request.user)
        except ValidationError as e:
            errors.extend(list(e.messages))
    
    if errors:
        return JsonResponse({'success': False, 'errors': errors}, status=400)
    
    request.user.set_password(new_password1)
    request.user.save()
    
    from django.contrib.auth import update_session_auth_hash
    update_session_auth_hash(request, request.user)
    
    return JsonResponse({'success': True, 'message': 'Password changed successfully.'})


@login_required(login_url='login')
def admin_profile(request):
    user = request.user

    if request.method == 'POST':
        first_name = (request.POST.get('first_name', '') or '').strip()
        last_name = (request.POST.get('last_name', '') or '').strip()
        email = (request.POST.get('email', '') or '').strip().lower()

        if not first_name:
            messages.error(request, 'First name is required.')
            return redirect('admin_profile')

        if not email:
            messages.error(request, 'Email address is required.')
            return redirect('admin_profile')

        duplicate_email = User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists()
        if duplicate_email:
            messages.error(request, 'Email is already in use by another account.')
            return redirect('admin_profile')

        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save(update_fields=['first_name', 'last_name', 'email'])

        messages.success(request, 'Profile information updated successfully.')
        return redirect('admin_profile')

    context = {
        'user': user,
    }
    return render(request, 'core/admin_profile.html', context)


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


def _require_lead_group(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        user_role = get_user_role(request.user)
        if user_role != 'lead':
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required(login_url='login')
def lead_dashboard(request):
    user_role = get_user_role(request.user)
    if user_role != 'lead':
        return redirect('dashboard')
    
    lead_profile = Lead.objects.filter(user=request.user).first()
    
    if not lead_profile:
        return redirect('lead_add_lead')
    
    applications = lead_profile.applications.select_related('program').order_by('-app_date')
    
    application_data = []
    for app in applications:
        program_name = app.program.name if app.program else '—'
        application_data.append({
            'id': app.app_id,
            'program': program_name,
            'status': app.get_status_display(),
            'status_key': app.status,
            'exam_score': str(app.exam_score) if app.exam_score else '—',
            'exam_result': app.get_exam_result_display() if app.exam_result else '—',
            'scholarship': f"{app.scholarship_percentage}%" if app.scholarship_percentage else '—',
            'final_fee': str(app.final_course_fee) if app.final_course_fee else '—',
            'submitted': app.app_date.strftime('%Y-%m-%d'),
        })
    
    status_steps = [
        {'key': 'new', 'label': 'Application Submitted', 'completed': True},
        {'key': 'qualified', 'label': 'Qualified', 'completed': lead_profile.current_status in ['qualified', 'followup', 'exams', 'enrolled']},
        {'key': 'followup', 'label': 'Under Review', 'completed': lead_profile.current_status in ['followup', 'exams', 'enrolled']},
        {'key': 'exams', 'label': 'Exams', 'completed': lead_profile.current_status in ['exams', 'enrolled']},
        {'key': 'enrolled', 'label': 'Enrolled', 'completed': lead_profile.current_status == 'enrolled'},
    ]
    
    context = {
        'lead': lead_profile,
        'applications': application_data,
        'status_steps': status_steps,
        'current_status': lead_profile.get_current_status_display(),
    }
    return render(request, 'core/lead_group/lead_dashboard.html', context)


@login_required(login_url='login')
def lead_add_lead(request):
    user_role = get_user_role(request.user)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if user_role != 'lead':
        if request.method == 'POST' and is_ajax:
            return JsonResponse({'success': False, 'error': 'Unauthorized access.'}, status=403)
        return redirect('dashboard')
    
    lead_profile = Lead.objects.filter(user=request.user).first()
    if lead_profile:
        if request.method == 'POST' and is_ajax:
            return JsonResponse({'success': False, 'error': 'Application already submitted.'}, status=400)
        return redirect('lead_dashboard')
    
    if request.method == 'POST':
        form = LeadSubmissionForm(request.POST, request.FILES, user_role='lead')
        if not form.is_valid():
            error_message = _first_form_error(form)
            if is_ajax:
                return JsonResponse({'success': False, 'error': error_message, 'errors': form.errors}, status=400)
            messages.error(request, error_message)
            return redirect('lead_add_lead')

        cleaned = form.cleaned_data

        try:
            with transaction.atomic():
                lead = Lead.objects.create(
                    user=request.user,
                    first_name=cleaned['first_name'],
                    last_name=cleaned['last_name'],
                    email=request.user.email or cleaned.get('email') or None,
                    phone=cleaned.get('phone') or None,
                    date_of_birth=cleaned.get('date_of_birth'),
                    gender=cleaned.get('gender') or None,
                    address=cleaned.get('address') or None,
                    nationality=cleaned.get('nationality') or None,
                    alternate_contact=cleaned.get('alternate_contact') or None,
                    program_interest=cleaned['program_interest'],
                    highest_education_level=cleaned['education_level'],
                    gpa_or_percentage=cleaned.get('gpa_or_percentage') or None,
                    previous_institution=cleaned.get('previous_institution') or None,
                    education_document=cleaned.get('education_document'),
                    scholarship_interest=cleaned.get('scholarship_interest') or None,
                    preferred_study_mode=cleaned.get('study_mode') or None,
                    source=cleaned['lead_source'],
                    current_status='new',
                )

                Application.objects.create(
                    lead=lead,
                    program=cleaned['program_obj'],
                    status='pending'
                )

                Notification.objects.create(
                    notification_type='new_lead',
                    title='New Lead Registration',
                    message=f'{lead.first_name} {lead.last_name} has registered as a new lead.',
                    link='/leads/'
                )
        except IntegrityError:
            if is_ajax:
                return JsonResponse({'success': False, 'error': 'Unable to save your application right now.'}, status=500)
            messages.error(request, 'Unable to save your application right now.')
            return redirect('lead_add_lead')

        messages.success(request, 'Your application has been submitted successfully!')
        if is_ajax:
            return JsonResponse({'success': True, 'redirect_url': '/lead/'})
        return redirect('lead_dashboard')

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

    return render(request, 'core/lead_group/lead_add_lead.html', {
        'department_programs': department_programs,
        'source_choices': Lead.SOURCE_CHOICES,
        'gender_choices': Lead.GENDER_CHOICES,
        'education_level_choices': Lead.EDUCATION_LEVEL_CHOICES,
        'scholarship_choices': Lead.SCHOLARSHIP_INTEREST_CHOICES,
        'study_mode_choices': Lead.STUDY_MODE_CHOICES,
    })
