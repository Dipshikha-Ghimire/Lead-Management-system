from .models import Staff


def sidebar_profile(request):
    user = request.user

    if not user.is_authenticated:
        return {'sidebar_profile': None}

    staff = Staff.objects.filter(email=user.email).first()

    full_name = (user.get_full_name() or '').strip()
    if not full_name and staff and staff.full_name:
        full_name = staff.full_name.strip()
    if not full_name:
        full_name = user.username

    role_label = staff.get_role_display() if staff else 'System User'
    email = user.email or (staff.email if staff else '') or 'No email set'

    return {
        'sidebar_profile': {
            'name': full_name,
            'email': email,
            'role': role_label,
        }
    }
