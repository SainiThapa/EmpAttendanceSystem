from django.http import HttpResponseForbidden
import ipaddress

class RestrictIPMiddleware:
    ALLOWED_IP_RANGE = '192.168.1.0/25' 

    def __init__(self, get_response):
        self.get_response = get_response
        self.allowed_network = ipaddress.ip_network(self.ALLOWED_IP_RANGE)

    def __call__(self, request):
        client_ip = self.get_client_ip(request)
        if request.path.startswith('/record-attendance/') and not self.is_allowed_ip(client_ip):
            return HttpResponseForbidden("Attendance recording is only allowed from the office Wi-Fi (192.168.1.1 to 192.168.1.126).")
        return self.get_response(request)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def is_allowed_ip(self, ip):
        try:
            client_ip = ipaddress.ip_address(ip)
            return client_ip in self.allowed_network
        except ValueError:
            return False