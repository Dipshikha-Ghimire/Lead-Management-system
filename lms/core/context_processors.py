from .models import Staff, Admin, Lead


def sidebar_profile(request):
    user = request.user

    if not user.is_authenticated:
        return {
            'sidebar_profile': None,
            'is_staff_user': False,
            'is_admin_user': False,
        }

    staff = Staff.objects.filter(email=user.email).first()
    admin_profile = Admin.objects.filter(email=user.email).first()
    lead_profile = Lead.objects.filter(user=user).first()

    full_name = (user.get_full_name() or '').strip()
    if not full_name and admin_profile and admin_profile.full_name:
        full_name = admin_profile.full_name.strip()
    elif not full_name and staff and staff.full_name:
        full_name = staff.full_name.strip()
    elif not full_name and lead_profile:
        full_name = f"{lead_profile.first_name} {lead_profile.last_name}".strip()
    if not full_name:
        full_name = user.username

    role_label = admin_profile.get_role_display() if admin_profile else (staff.get_role_display() if staff else 'Lead User')
    email = user.email or (admin_profile.email if admin_profile else '') or (staff.email if staff else '') or (lead_profile.email if lead_profile else 'No email set')

    user_groups = user.groups.values_list('name', flat=True)
    is_lead = 'lead' in user_groups
    is_staff_user = 'staff' in user_groups and not user.is_superuser and not admin_profile
    is_admin_user = user.is_superuser or ('admin' in user_groups) or (admin_profile is not None)

    return {
        'sidebar_profile': {
            'name': full_name,
            'email': email,
            'role': role_label,
            'is_lead': is_lead,
        },
        'is_staff_user': is_staff_user,
        'is_admin_user': is_admin_user,
    }
