from test_base import MainTestCase
from test_process import TestSite
from main.models import UserProfile
from main.views import show, edit
from django.core.urlresolvers import reverse
from odk_logger.models import XForm
import os

class TestFormShow(MainTestCase):

    def setUp(self):
        MainTestCase.setUp(self)
        self._create_user_and_login()
        xls_path = os.path.join(self.this_directory, "fixtures",
                "transportation", "transportation.xls")
        response = self._publish_xls_file(xls_path)
        self.assertEqual(XForm.objects.count(), 1)
        self.xform = XForm.objects.all()[0]
        self.url = reverse(show, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        })

    def test_show_form_name(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.xform.id_string)

    def test_hide_from_anon(self):
        response = self.anon.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_show_to_anon_if_public(self):
        self.xform.shared = True
        self.xform.save()
        response = self.anon.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.xform.id_string)

    def test_show_private_if_shared_but_not_data(self):
        self.xform.shared = True
        self.xform.save()
        response = self.anon.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.xform.id_string)
        self.assertContains(response, 'PRIVATE')

    def test_show_link_if_shared_and_data(self):
        self.xform.shared = True
        self.xform.shared_data = True
        self.xform.save()
        response = self.anon.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.xform.id_string)
        self.assertNotContains(response, 'PRIVATE')
        self.assertContains(response, '/%s/data.csv' % self.xform.id_string)

    def test_user_sees_edit_btn(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.xform.id_string)
        self.assertContains(response, 'edit</a>')

    def test_anon_no_edit_btn(self):
        self.xform.shared = True
        self.xform.save()
        response = self.anon.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.xform.id_string)
        self.assertNotContains(response, 'edit</a>')

    def test_anon_no_edit_post(self):
        self.xform.shared = True
        self.xform.save()
        url = reverse(edit, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        })
        desc = 'Snooky'
        response = self.anon.post(url, {'description': desc})
        self.assertNotEqual(XForm.objects.get(pk=self.xform.pk).description, desc)
        self.assertEqual(response.status_code, 302)

    def test_not_owner_no_edit_post(self):
        self.xform.shared = True
        self.xform.save()
        url = reverse(edit, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        })
        desc = 'Snooky'
        self._create_user_and_login("jo")
        response = self.client.post(url, {'description': desc})
        self.assertEqual(response.status_code, 405)
        self.assertNotEqual(XForm.objects.get(pk=self.xform.pk).description, desc)

    def test_user_edit_post_updates(self):
        url = reverse(edit, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        })
        desc = 'Snooky'
        response = self.client.post(url, {'description': desc})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(XForm.objects.get(pk=self.xform.pk).description, desc)

