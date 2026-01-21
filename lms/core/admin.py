from django.contrib import admin
from .models import (
    Department, Program, Staff, Lead, FollowUp,
    Application, EntranceExam, Scholarship, Payment
)

admin.site.register(Department)
admin.site.register(Program)
admin.site.register(Staff)
admin.site.register(Lead)
admin.site.register(FollowUp)
admin.site.register(Application)
admin.site.register(EntranceExam)
admin.site.register(Scholarship)
admin.site.register(Payment)
