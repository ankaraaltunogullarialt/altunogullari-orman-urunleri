from django.shortcuts import redirect

from fabrika.roles import is_portal_user


def portal_access_middleware(get_response):
    """Portal kullanıcılarının sadece rapor sayfalarına erişmesine izin verir."""

    def middleware(request):
        protected_prefixes = (
            '/stok/rapor/',
            '/personel/rapor/',
            '/siparis/satis-raporu/',
        )

        exempt_prefixes = (
            '/admin/',
            '/portal/',
            '/static/',
            '/media/',
        )

        path = request.path

        if any(path.startswith(prefix) for prefix in exempt_prefixes):
            return get_response(request)

        if any(path.startswith(prefix) for prefix in protected_prefixes):
            if not request.user.is_authenticated:
                return redirect(f'/portal/login/?next={request.get_full_path()}')

            if request.user.is_staff:
                return get_response(request)

            if not is_portal_user(request.user):
                return redirect(f'/portal/login/?next={request.get_full_path()}')

        return get_response(request)

    return middleware
