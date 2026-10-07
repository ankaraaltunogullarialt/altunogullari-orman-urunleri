from django.contrib.auth.models import Group

GROUP_NAME_ADMIN = 'Yönetici'
GROUP_NAME_PORTAL = 'Portal Kullanıcısı'
GROUP_NAME_STOK = 'Stok Sorumlusu'
GROUP_NAME_SATIS = 'Satış Sorumlusu'
GROUP_NAME_MUDUR = 'Müdür'

DEFAULT_ROLE_GROUPS = {
    'admin': GROUP_NAME_ADMIN,
    'portal': GROUP_NAME_PORTAL,
    'stok': GROUP_NAME_STOK,
    'satis': GROUP_NAME_SATIS,
    'mudur': GROUP_NAME_MUDUR,
}


def ensure_default_groups():
    """Varsayılan Türkçe rol gruplarını garanti eder."""
    for group_name in DEFAULT_ROLE_GROUPS.values():
        Group.objects.get_or_create(name=group_name)


def is_portal_user(user):
    """Kullanıcının portal rolüne sahip olup olmadığını kontrol eder."""
    if user is None or not user.is_authenticated:
        return False
    return user.groups.filter(name=GROUP_NAME_PORTAL).exists() or user.groups.filter(name='portal').exists()


def is_admin_user(user):
    """Kullanıcının yönetici rolüne sahip olup olmadığını kontrol eder."""
    if user is None or not user.is_authenticated:
        return False
    return user.is_staff or user.groups.filter(name=GROUP_NAME_ADMIN).exists()
