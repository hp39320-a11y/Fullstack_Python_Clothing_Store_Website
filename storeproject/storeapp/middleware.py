from django.shortcuts import redirect


class RoleBasedAccessMiddleware:
    """
    Middleware to enforce role-based access control, preventing non-staff
    authenticated users from accessing administrative URL patterns.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Prevent authenticated non-staff users from accessing administrative urls
        if request.path.startswith('/admin'):
            if request.user.is_authenticated and not request.user.is_staff:
                return redirect('index')

        return self.get_response(request)