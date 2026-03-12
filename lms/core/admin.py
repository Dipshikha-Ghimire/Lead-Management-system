from django.contrib import admin
from django.db.models import Sum
from django.utils import timezone
from django.utils.html import format_html
from .models import (
    Department, Program, Staff, Lead, FollowUp,
    Application, EntranceExam, Scholarship, Payment
)


_original_each_context = admin.site.each_context


def _custom_admin_each_context(request):
    context = _original_each_context(request)
    today = timezone.localdate()

    lead_status_summary = [
        {'label': 'New', 'count': Lead.objects.filter(current_status='new').count(), 'tone': 'new'},
        {'label': 'Qualified', 'count': Lead.objects.filter(current_status='qualified').count(), 'tone': 'qualified'},
        {'label': 'Converted', 'count': Lead.objects.filter(current_status='converted').count(), 'tone': 'converted'},
        {'label': 'Dropped', 'count': Lead.objects.filter(current_status='dropped').count(), 'tone': 'dropped'},
    ]

    application_status_summary = [
        {'label': 'Pending', 'count': Application.objects.filter(status='pending').count(), 'tone': 'pending'},
        {'label': 'Reviewed', 'count': Application.objects.filter(status='reviewed').count(), 'tone': 'reviewed'},
        {'label': 'Accepted', 'count': Application.objects.filter(status='accepted').count(), 'tone': 'accepted'},
        {'label': 'Rejected', 'count': Application.objects.filter(status='rejected').count(), 'tone': 'rejected'},
    ]

    payment_verified_total = Payment.objects.filter(status='verified').aggregate(total=Sum('amount')).get('total')

    context.update({
        'admin_metrics': {
            'lead_count': Lead.objects.count(),
            'application_count': Application.objects.count(),
            'pending_applications': Application.objects.filter(status='pending').count(),
            'due_followups': Lead.objects.filter(followup_date__isnull=False, followup_date__lte=today).count(),
            'payment_verified_count': Payment.objects.filter(status='verified').count(),
            'payment_verified_total': payment_verified_total or 0,
        },
        'lead_status_summary': lead_status_summary,
        'application_status_summary': application_status_summary,
    })
    return context


admin.site.each_context = _custom_admin_each_context


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'phone')
    search_fields = ('name', 'location', 'phone')
    ordering = ('name',)


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('name', 'dept', 'duration_years', 'total_fee')
    search_fields = ('name', 'dept__name')
    ordering = ('name',)
    autocomplete_fields = ('dept',)


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'role')
    search_fields = ('full_name', 'email')
    ordering = ('full_name',)


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = (
        'lead_id',
        'first_name',
        'last_name',
        'program_interest',
        'phone',
        'email',
        'source',
        'status_badge',
        'assigned_staff',
        'followup_date',
        'created_at'
    )
    search_fields = ('first_name', 'last_name', 'phone', 'email', 'program_interest', 'nationality')
    list_per_page = 20
    ordering = ('-created_at',)
    list_select_related = ('assigned_staff',)
    autocomplete_fields = ('assigned_staff',)
    readonly_fields = ('created_at',)
    actions = ('mark_as_qualified', 'mark_as_converted')

    fieldsets = (
        ('Identity', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'alternate_contact')
        }),
        ('Profile', {
            'fields': ('date_of_birth', 'gender', 'nationality', 'address')
        }),
        ('Academic', {
            'fields': (
                'program_interest',
                'desired_intake_year',
                'intake_semester',
                'highest_education_level',
                'gpa_or_percentage',
                'previous_institution',
                'scholarship_interest',
                'preferred_study_mode',
            )
        }),
        ('Lead Management', {
            'fields': ('source', 'current_status', 'assigned_staff', 'followup_date', 'notes')
        }),
        ('System', {
            'fields': ('created_at',)
        }),
    )

    @admin.display(description='Status', ordering='current_status')
    def status_badge(self, obj):
        tones = {
            'new': 'tone-new',
            'qualified': 'tone-qualified',
            'converted': 'tone-converted',
            'dropped': 'tone-dropped',
        }
        css_class = tones.get(obj.current_status, 'tone-default')
        return format_html('<span class="admin-badge {}">{}</span>', css_class, obj.get_current_status_display())

    @admin.action(description='Mark selected leads as Qualified')
    def mark_as_qualified(self, request, queryset):
        queryset.update(current_status='qualified')

    @admin.action(description='Mark selected leads as Converted')
    def mark_as_converted(self, request, queryset):
        queryset.update(current_status='converted')


@admin.register(FollowUp)
class FollowUpAdmin(admin.ModelAdmin):
    list_display = ('lead', 'staff', 'mode', 'followup_date', 'next_action_date')
    search_fields = ('lead__first_name', 'lead__last_name', 'staff__full_name', 'remarks')
    ordering = ('-followup_date',)
    autocomplete_fields = ('lead', 'staff')


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('app_id', 'lead', 'program', 'status_badge', 'app_date')
    search_fields = ('lead__first_name', 'lead__last_name', 'program__name')
    ordering = ('-app_date',)
    autocomplete_fields = ('lead', 'program')
    actions = ('mark_as_reviewed', 'mark_as_accepted')

    @admin.display(description='Status', ordering='status')
    def status_badge(self, obj):
        tones = {
            'pending': 'tone-pending',
            'reviewed': 'tone-reviewed',
            'accepted': 'tone-accepted',
            'rejected': 'tone-rejected',
        }
        css_class = tones.get(obj.status, 'tone-default')
        return format_html('<span class="admin-badge {}">{}</span>', css_class, obj.get_status_display())

    @admin.action(description='Mark selected applications as Reviewed')
    def mark_as_reviewed(self, request, queryset):
        queryset.update(status='reviewed')

    @admin.action(description='Mark selected applications as Accepted')
    def mark_as_accepted(self, request, queryset):
        queryset.update(status='accepted')


@admin.register(EntranceExam)
class EntranceExamAdmin(admin.ModelAdmin):
    list_display = ('exam_id', 'application', 'type', 'score', 'result_status', 'exam_date')
    search_fields = ('application__lead__first_name', 'application__lead__last_name')
    ordering = ('-exam_date',)
    autocomplete_fields = ('application',)


@admin.register(Scholarship)
class ScholarshipAdmin(admin.ModelAdmin):
    list_display = ('schol_id', 'exam', 'type', 'percentage_off', 'is_approved')
    search_fields = ('exam__application__lead__first_name', 'exam__application__lead__last_name')
    autocomplete_fields = ('exam',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('pay_id', 'lead', 'application', 'amount', 'payment_type', 'method', 'status_badge', 'payment_date')
    search_fields = (
        'lead__first_name',
        'lead__last_name',
        'transaction_ref_id',
        'application__program__name',
    )
    ordering = ('-payment_date',)
    autocomplete_fields = ('lead', 'application')
    actions = ('mark_as_verified',)

    @admin.display(description='Status', ordering='status')
    def status_badge(self, obj):
        tones = {
            'pending': 'tone-pending',
            'verified': 'tone-accepted',
            'failed': 'tone-rejected',
        }
        css_class = tones.get(obj.status, 'tone-default')
        return format_html('<span class="admin-badge {}">{}</span>', css_class, obj.get_status_display())

    @admin.action(description='Mark selected payments as Verified')
    def mark_as_verified(self, request, queryset):
        queryset.update(status='verified')


admin.site.site_header = 'LMS Administration'
admin.site.site_title = 'LMS Admin'
admin.site.index_title = 'Lead & Admissions Management'
