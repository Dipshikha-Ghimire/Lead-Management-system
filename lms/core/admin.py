from django.contrib import admin
from .models import (
    Department, Program, Staff, Lead, FollowUp,
    Application, EntranceExam, Scholarship, Payment
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'phone')
    search_fields = ('name', 'location', 'phone')
    ordering = ('name',)


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('name', 'dept', 'duration_years', 'total_fee')
    list_filter = ('dept',)
    search_fields = ('name', 'dept__name')
    ordering = ('name',)
    autocomplete_fields = ('dept',)


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'role')
    list_filter = ('role',)
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
        'current_status',
        'assigned_staff',
        'followup_date',
        'created_at'
    )
    list_filter = ('current_status', 'source', 'preferred_study_mode', 'assigned_staff', 'created_at')
    search_fields = ('first_name', 'last_name', 'phone', 'email', 'program_interest', 'nationality')
    list_per_page = 20
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_select_related = ('assigned_staff',)
    autocomplete_fields = ('assigned_staff',)
    readonly_fields = ('created_at',)

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


@admin.register(FollowUp)
class FollowUpAdmin(admin.ModelAdmin):
    list_display = ('lead', 'staff', 'mode', 'followup_date', 'next_action_date')
    list_filter = ('mode', 'followup_date', 'staff')
    search_fields = ('lead__first_name', 'lead__last_name', 'staff__full_name', 'remarks')
    ordering = ('-followup_date',)
    date_hierarchy = 'followup_date'
    autocomplete_fields = ('lead', 'staff')


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('app_id', 'lead', 'program', 'status', 'app_date')
    list_filter = ('status', 'program__dept')
    search_fields = ('lead__first_name', 'lead__last_name', 'program__name')
    ordering = ('-app_date',)
    date_hierarchy = 'app_date'
    autocomplete_fields = ('lead', 'program')


@admin.register(EntranceExam)
class EntranceExamAdmin(admin.ModelAdmin):
    list_display = ('exam_id', 'application', 'type', 'score', 'result_status', 'exam_date')
    list_filter = ('type', 'result_status')
    search_fields = ('application__lead__first_name', 'application__lead__last_name')
    ordering = ('-exam_date',)
    date_hierarchy = 'exam_date'
    autocomplete_fields = ('application',)


@admin.register(Scholarship)
class ScholarshipAdmin(admin.ModelAdmin):
    list_display = ('schol_id', 'exam', 'type', 'percentage_off', 'is_approved')
    list_filter = ('type', 'is_approved')
    search_fields = ('exam__application__lead__first_name', 'exam__application__lead__last_name')
    autocomplete_fields = ('exam',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('pay_id', 'lead', 'application', 'amount', 'payment_type', 'method', 'status', 'payment_date')
    list_filter = ('status', 'payment_type', 'method', 'payment_date')
    search_fields = (
        'lead__first_name',
        'lead__last_name',
        'transaction_ref_id',
        'application__program__name',
    )
    ordering = ('-payment_date',)
    date_hierarchy = 'payment_date'
    autocomplete_fields = ('lead', 'application')


admin.site.site_header = 'LMS Administration'
admin.site.site_title = 'LMS Admin'
admin.site.index_title = 'Lead & Admissions Management'
