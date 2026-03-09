from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),          # homepage
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
    path('exams/', views.exams, name='exams'),
    path('finance/', views.finance, name='finance'),
    path('settings/', views.settings, name='settings'),
]
