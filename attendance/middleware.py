from django.http import HttpResponseForbidden

class RestrictIPMiddleware:
    ALLOWED_IP = '27.34.64.212'

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        client_ip = self.get_client_ip(request)
        if request.path.startswith('/record-attendance/') and client_ip != self.ALLOWED_IP:
            return HttpResponseForbidden("Access denied: This endpoint is restricted to the authorized IP address.")
        return self.get_response(request)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Use the first IP in the list if behind a proxy
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
