from django.test import Client, TestCase
from django.contrib.auth.models import User, Group

from fabrika.roles import (
    DEFAULT_ROLE_GROUPS,
    GROUP_NAME_ADMIN,
    GROUP_NAME_PORTAL,
    ensure_default_groups,
    is_portal_user,
)


class PortalLoginRedirectTests(TestCase):
    def test_portal_user_redirects_to_dashboard_after_login(self):
        portal_group, _ = Group.objects.get_or_create(name=GROUP_NAME_PORTAL)
        user = User.objects.create_user(username='portaluser', password='secret123')
        user.groups.add(portal_group)

        client = Client()
        response = client.post('/portal/login/', {'username': 'portaluser', 'password': 'secret123'}, follow=False)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/portal/')

    def test_default_turkish_role_groups_are_created(self):
        ensure_default_groups()
        self.assertIn(GROUP_NAME_PORTAL, [group.name for group in Group.objects.all()])
        self.assertIn(DEFAULT_ROLE_GROUPS['admin'], [group.name for group in Group.objects.all()])

    def test_portal_group_helper_detects_portal_users(self):
        group, _ = Group.objects.get_or_create(name=GROUP_NAME_PORTAL)
        user = User.objects.create_user(username='portalhelper', password='secret123')
        user.groups.add(group)

        self.assertTrue(is_portal_user(user))
