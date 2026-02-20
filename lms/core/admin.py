from django.contrib import admin
from .models import (
    Department, Program, Staff, Lead, FollowUp,
    Application, EntranceExam, Scholarship, Payment
)

admin.site.register(Department)
admin.site.register(Program)
admin.site.register(Staff)
@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = (
        'first_name',
        'last_name',
        'phone',
        'email',
        'source',
        'current_status',
        'assigned_staff',
        'created_at'
    )
    list_filter = ('current_status', 'source', 'assigned_staff')
    search_fields = ('first_name', 'last_name', 'phone', 'email')
    list_per_page = 20
admin.site.register(FollowUp)
admin.site.register(Application)
admin.site.register(EntranceExam)
admin.site.register(Scholarship)
admin.site.register(Payment)
