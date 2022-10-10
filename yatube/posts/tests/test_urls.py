from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post_author = User.objects.create_user(username='Leo')
        cls.non_author = User.objects.create_user(username='Olga')
        cls.group = Group.objects.create(
            title='test-group',
            slug='test-slug',
            description='test-description',
        )
        cls.post = Post.objects.create(
            author=cls.post_author,
            text='test-post',
            id=50,
        )
        cls.url_index = '/'
        cls.url_group = f'/group/{cls.group.slug}/'
        cls.url_profile = f'/profile/{cls.non_author}/'
        cls.url_post_detail = f'/posts/{cls.post.id}/'
        cls.url_create = '/create/'
        cls.url_edit = f'/posts/{cls.post.id}/edit/'

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.post_author)
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.non_author)
        cache.clear()

    def test_status_code_al_users(self):
        """Страницы доступны любому пользователю."""
        urls = (
            self.url_index,
            self.url_group,
            self.url_profile,
            self.url_post_detail,
        )
        for url in urls:
            response = self.guest_client.get(url)
            error_name = f'Ошибка: нет доступа до страницы {urls}'

            self.assertEqual(response.status_code, HTTPStatus.OK, error_name)

    def test_status_code_auth_users(self):
        """Страницы доступны авторизованному пользователю."""
        urls = (
            self.url_index,
            self.url_group,
            self.url_profile,
            self.url_post_detail,
            self.url_create,
        )
        for url in urls:
            response = self.authorized_client_2.get(url)
            error_name = f'Ошибка: нет доступа до страницы {url}'

            self.assertEqual(response.status_code, HTTPStatus.OK, error_name)

    def test_status_code_edit_for_author(self):
        """Страница доступна автору."""
        url = self.url_edit
        response = self.authorized_client.get(url)
        error_name = f'Ошибка: нет доступа до страницы {url}'

        self.assertEqual(response.status_code, HTTPStatus.OK, error_name)

    def test_redirect_anonymous_login(self):
        """Redirect анонимного пользователя на страницу логина."""
        urls_redirect = {
            self.url_create: '/auth/login/?next=/create/',
            self.url_edit: f'/auth/login/?next=/posts/{self.post.id}/edit/',
        }
        for url, redirect in urls_redirect.items():
            response = self.guest_client.get(url, follow=True)

            with self.subTest(url=url):
                self.assertRedirects(response, redirect)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_edit_not_author_correct_template(self):
        """Redirect страницы редактирования
         поста не автора поста."""
        response = self.authorized_client_2.get(self.url_edit, follow=True)
        redirect = f'/posts/{self.post.id}/'

        self.assertRedirects(response, redirect)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            self.url_index: 'posts/index.html',
            self.url_group: 'posts/group_list.html',
            self.url_profile: 'posts/profile.html',
            self.url_post_detail: 'posts/post_detail.html',
            self.url_create: 'posts/post_create.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client_2.get(address)
                error_name = f'Ошибка: {address} ожидал шаблон {template}'

                self.assertTemplateUsed(response, template, error_name)

    def test_url_edit_uses_correct_template(self):
        """URL-адрес, доступный только автору
         использует соответствующий шаблон."""
        response = self.authorized_client.get(self.url_edit)
        error_name = 'Ошибка: адрес ожидал шаблон posts/post_create.html'

        self.assertTemplateUsed(response, 'posts/post_create.html', error_name)

    def test_wrong_url_returns_404(self):
        """Запрос к несуществующей странице вернет ошибку 404."""
        response = self.guest_client.get('something/really/')

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
