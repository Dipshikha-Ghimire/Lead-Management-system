from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='core/password_reset.html',
        email_template_name='registration/password_reset_email.html',
        subject_template_name='registration/password_reset_subject.txt'
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='core/password_reset_done.html'
    ), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='core/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='core/password_reset_complete.html'
    ), name='password_reset_complete'),

    path('dashboard/', views.dashboard, name='dashboard'),
    path('staff/dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('leads/', views.leads, name='leads'),
    path('leads/add_lead/', views.lead_form, name='lead_form'),
    path('leads/<int:lead_id>/', views.lead_detail_api, name='lead_detail_api'),
    path('leads/<int:lead_id>/update/', views.lead_update_api, name='lead_update_api'),
    path('leads/<int:lead_id>/delete/', views.lead_delete_api, name='lead_delete_api'),
    path('applications/', views.applications, name='applications'),
    path('applications/create/', views.application_create_api, name='application_create_api'),
    path('applications/<int:app_id>/', views.application_detail_api, name='application_detail_api'),
    path('applications/<int:app_id>/update/', views.application_update_api, name='application_update_api'),
    path('applications/<int:app_id>/delete/', views.application_delete_api, name='application_delete_api'),
    path('applications/<int:app_id>/action/', views.application_action_api, name='application_action_api'),
    path('applications/<int:app_id>/approve/', views.application_approve_api, name='application_approve_api'),
    path('applications/<int:app_id>/reject/', views.application_reject_api, name='application_reject_api'),
    path('applications/<int:app_id>/restore/', views.application_restore_api, name='application_restore_api'),
    path('applications/<int:app_id>/permanent-delete/', views.application_permanent_delete_api, name='application_permanent_delete_api'),
    path('exams/', views.exams, name='exams'),
    path('exams/detail/', views.exam_detail_api, name='exam_detail_api'),
    path('exams/submit/', views.submit_exam_info, name='submit_exam_info'),
    path('exams/approve-scholarship/', views.approve_scholarship, name='approve_scholarship'),
    path('exams/disapprove-scholarship/', views.disapprove_scholarship, name='disapprove_scholarship'),
    path('courses/', views.courses, name='courses'),
    path('courses/department/add/', views.department_add_api, name='department_add_api'),
    path('courses/department/<int:dept_id>/update/', views.department_update_api, name='department_update_api'),
    path('courses/department/<int:dept_id>/delete/', views.department_delete_api, name='department_delete_api'),
    path('courses/program/add/', views.program_add_api, name='program_add_api'),
    path('courses/program/<int:prog_id>/update/', views.program_update_api, name='program_update_api'),
    path('courses/program/<int:prog_id>/delete/', views.program_delete_api, name='program_delete_api'),
    path('profile/', views.profile, name='profile'),
    path('admin-profile/', views.admin_profile, name='admin_profile'),
    path('change-password/', views.change_password_api, name='change_password_api'),
    path('settings/', views.settings, name='settings'),
    path('notifications/', views.notifications_api, name='notifications_api'),
    path('notifications/<int:notif_id>/read/', views.mark_notification_read_api, name='mark_notification_read_api'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read_api, name='mark_all_notifications_read_api'),
    
    path('lead/', views.lead_dashboard, name='lead_dashboard'),
    path('lead/add/', views.lead_add_lead, name='lead_add_lead'),
]
