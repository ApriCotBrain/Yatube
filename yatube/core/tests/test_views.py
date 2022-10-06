from django.test import Client, TestCase


class CoreViewTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_page_404_custom_template(self):
        """Страница 404 отдает кастомный шаблон."""
        response = self.guest_client.get('something/really/')

        self.assertTemplateUsed(response, 'core/404.html')
