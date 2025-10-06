# shipments/tz_middleware.py
from django.utils import timezone
from zoneinfo import ZoneInfo 

# Middleware to set timezone from request header, query param, or user profile
class TimezoneMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tzname = request.headers.get("X-Timezone") or request.GET.get("tz")

        # دعم أوفست بالدقائق كبديل
        if not tzname:
            offset = request.headers.get("X-TZ-Offset")
            if offset:
                try:
                    tz = timezone.get_fixed_timezone(int(offset))
                    timezone.activate(tz)
                    resp = self.get_response(request)
                    timezone.deactivate()
                    return resp
                except Exception:
                    pass

        if not tzname and getattr(request, "user", None) and request.user.is_authenticated:
            tzname = getattr(request.user, "timezone", None)

        tzname = tzname or "Asia/Riyadh"

        try:
            timezone.activate(ZoneInfo(tzname))
        except Exception:
            timezone.activate(ZoneInfo("Asia/Riyadh"))

        resp = self.get_response(request)
        timezone.deactivate()
        return resp
