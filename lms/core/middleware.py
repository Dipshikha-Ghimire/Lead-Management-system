from django.shortcuts import redirect


class LeadGroupAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        
        if user.is_authenticated and user.groups.filter(name='lead').exists():
            path = request.path
            
            if not path.startswith('/login') and not path.startswith('/logout'):
                if not path.startswith('/lead/'):
                    from core.models import Lead
                    lead_profile = Lead.objects.filter(user=user).first()
                    
                    if lead_profile:
                        return redirect('lead_dashboard')
                    else:
                        return redirect('lead_add_lead')
        
        return self.get_response(request)


class StaffGroupAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        
        if user.is_authenticated:
            is_admin = user.is_superuser or user.groups.filter(name='admin').exists()
            is_staff = user.groups.filter(name='staff').exists()
            is_lead = user.groups.filter(name='lead').exists()
            
            path = request.path
            
            if is_admin:
                return self.get_response(request)
            
            if is_staff:
                restricted_paths = [
                    '/courses/',
                ]
                
                if any(path.startswith(p) for p in restricted_paths):
                    return redirect('staff_dashboard')
                
                if path == '/dashboard/' or path == '/dashboard':
                    return redirect('staff_dashboard')
                
                return self.get_response(request)
            
            if is_lead:
                if path.startswith('/dashboard/') or path.startswith('/leads/') or path.startswith('/courses/'):
                    from core.models import Lead
                    lead_profile = Lead.objects.filter(user=user).first()
                    
                    if lead_profile:
                        return redirect('lead_dashboard')
                    else:
                        return redirect('lead_add_lead')
                
                if path.startswith('/applications/') and not path.endswith('/create/'):
                    from core.models import Lead
                    lead_profile = Lead.objects.filter(user=user).first()
                    
                    if lead_profile:
                        return redirect('lead_dashboard')
                    else:
                        return redirect('lead_add_lead')
        
        return self.get_response(request)
