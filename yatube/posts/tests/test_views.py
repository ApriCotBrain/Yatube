import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Follow, Post


User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Leo')
        cls.non_author = User.objects.create_user(username='Olga')
        cls.group_1 = Group.objects.create(
            title='test-group-1',
            slug='test-slug-1',
            description='test-description-1',
        )
        cls.group_2 = Group.objects.create(
            title='test-group-2',
            slug='test-slug-2',
            description='test-description-2',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            group=cls.group_1,
            text='test-post',
            id=50,
            image=cls.uploaded,
        )
        cls.follow = Follow.objects.create(
            author=cls.author,
            user=cls.non_author,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client_non_author = Client()
        self.authorized_client_non_author.force_login(self.non_author)
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.author)
        self.url_index = 'posts:index'
        self.url_group = 'posts:group_posts'
        self.url_profile = 'posts:profile'
        self.url_post_detail = 'posts:post_detail'
        self.url_create = 'posts:post_create'
        self.url_edit = 'posts:post_edit'
        self.url_follow_index = 'posts:follow_index'
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_urls_names = {
            reverse(self.url_index): 'posts/index.html',
            reverse(self.url_group,
                    kwargs={
                        'slug': self.group_1.slug}): 'posts/group_list.html',
            reverse(self.url_profile,
                    kwargs={
                        'username': self.non_author}): 'posts/profile.html',
            reverse(self.url_post_detail,
                    kwargs={
                        'post_id': self.post.id}): 'posts/post_detail.html',
            reverse(self.url_create): 'posts/post_create.html',
            reverse(self.url_edit,
                    kwargs={
                        'post_id': self.post.id}): 'posts/post_create.html',
        }

        for reverse_name, template in templates_urls_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client_author.get(reverse_name)
                error_name = f'Ошибка: {reverse_name} ожидал шаблон {template}'
                self.assertTemplateUsed(response, template, error_name)

    def test_index_show_correct_context(self):
        """Шаблон index сформированы с правильным контекстом."""
        response = self.authorized_client_non_author.get(
            reverse(self.url_index))
        first_object = {
            response.context['page_obj'][0].text: self.post.text,
            response.context['page_obj'][0].group: self.post.group,
            response.context['page_obj'][0].author: self.post.author,
            response.context['page_obj'][0].image: self.post.image,
        }

        for value, expected in first_object.items():
            self.assertEqual(first_object[value], expected)

    def test_group_show_correct_context(self):
        """Шаблон group сформирован
         с правильным контекстом."""
        response = self.authorized_client_non_author.get(
            reverse(self.url_group, kwargs={
                'slug': self.group_1.slug}))
        first_object = {
            response.context['group'].title: self.group_1.title,
            response.context['group'].slug: self.group_1.slug,
            response.context['page_obj'][0].text: self.post.text,
            response.context['page_obj'][0].group: self.post.group,
            response.context['page_obj'][0].author: self.post.author,
            response.context['page_obj'][0].image: self.post.image,
        }

        for value, expected in first_object.items():
            self.assertEqual(first_object[value], expected)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформированы с правильным контекстом."""
        response = self.authorized_client_non_author.get(
            reverse(self.url_profile, kwargs={
                'username': self.post.author}))
        first_object = {
            response.context['author'].username: self.post.author,
            response.context['page_obj'][0].text: self.post.text,
            response.context['page_obj'][0].group.title: self.group_1,
            response.context['page_obj'][0].author: self.post.author,
            response.context['page_obj'][0].image: self.post.image,
        }

        for value, expected in first_object.items():
            self.assertEqual(first_object[value], expected)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client_non_author.get(
            reverse(self.url_post_detail,
                    kwargs={'post_id': self.post.id}))
        first_object = {
            response.context['post']: self.post,
            response.context['posts_count']: self.post.author.posts.count(),
        }

        for value, expected in first_object.items():
            self.assertEqual(first_object[value], expected)

    def test_post_create_show_correct_context(self):
        """Шаблон создания поста
        сформирован с правильным контекстом форм."""
        response = self.authorized_client_author.get(
            reverse(self.url_create))
        form = response.context.get('form')

        self.assertIsInstance(form, forms.ModelForm)
        self.assertFalse(response.context.get('is_edit'))

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client_author.get(
            reverse(self.url_edit, kwargs={
                'post_id': self.post.id}))
        form = response.context.get('form')
        post_test = response.context['post_id']

        self.assertEqual(post_test, self.post.id)
        self.assertIsInstance(form, forms.ModelForm)
        self.assertTrue(response.context.get('is_edit'))

    def test_group_correct_display_in_index(self):
        """При выборе групп пост корректно
         отображается на странице index."""
        post = Post.objects.create(
            author=self.post.author,
            group=self.post.group,
            text='test-text',
        )

        response_index = self.authorized_client_non_author.get(
            reverse(self.url_index))
        index = response_index.context['page_obj']

        self.assertIn(post, index)

    def test_group_correct_display_in_group_posts(self):
        """При выборе групп пост корректно
         отображается на странице группы."""
        post = Post.objects.create(
            author=self.post.author,
            group=self.post.group,
            text='test-text',
        )

        response_group_posts = self.authorized_client_non_author.get(
            reverse(self.url_group, kwargs={
                'slug': self.post.group.slug}))
        group_post = response_group_posts.context['page_obj']

        self.assertIn(post, group_post)

    def test_group_correct_display_in_profile(self):
        """При выборе групп пост корректно
         отображается на странице profile."""
        post = Post.objects.create(
            author=self.post.author,
            group=self.post.group,
            text='test-text',
        )

        response_profile = self.authorized_client_non_author.get(
            reverse(self.url_profile, kwargs={
                'username': self.post.author}))
        profile = response_profile.context['page_obj']

        self.assertIn(post, profile)

    def test_post_not_in_incorrect_group(self):
        """Пост не попал в группу,
         для которой не предназначен."""
        post = Post.objects.create(
            author=self.post.author,
            group=self.group_1,
            text='test-text',
        )

        response_incorrect_group = self.authorized_client_non_author.get(
            reverse(self.url_group, kwargs={
                'slug': self.group_2.slug}))
        incorrect_group = response_incorrect_group.context['page_obj']

        self.assertNotIn(post, incorrect_group)

    def test_cache_index(self):
        """Проверка работы кэша для index."""
        response_before_cached = self.authorized_client_non_author.get(
            reverse(self.url_index))
        posts = response_before_cached.content
        post = Post.objects.create(
            author=self.post.author,
            group=self.group_1,
            text='test-text',
        )
        response_cached = self.authorized_client_non_author.get(
            reverse(self.url_index))
        cached_content = response_cached.content

        self.assertEqual(cached_content, posts)
        cache.clear()
        response_clear_cache = self.authorized_client_non_author.get(
            reverse(self.url_index))
        clear_cached_content = response_clear_cache.content

        self.assertNotEqual(cached_content, clear_cached_content)
        self.assertIn(post, response_clear_cache.context['page_obj'])

    def test_follow_authorized_client(self):
        """Авторизованный пользователь может подписываться
         на других пользователей."""
        follow_count = Follow.objects.count()

        response = self.authorized_client_non_author.post(
            reverse('posts:profile_follow',
                    kwargs={'username': self.author}))
        redirect = f'/profile/{self.author}/'

        self.assertRedirects(response, redirect)
        self.assertEqual(Follow.objects.count(), follow_count)

    def test_unfollow_authorized_client(self):
        """Авторизованный пользователь может
        удалять других пользователей из подписок"""
        follow_count = Follow.objects.count()

        response = self.authorized_client_non_author.post(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.author}))
        redirect = '/follow/'

        self.assertRedirects(response, redirect)
        self.assertEqual(Follow.objects.count(), follow_count - 1)

    def test_follow_correct_display_in_follow_index(self):
        """Новая запись пользователя появляется
         в ленте тех, кто на него подписан."""
        post = Post.objects.create(
            author=self.author,
            text='test-text',
        )

        response_follow_index = self.authorized_client_non_author.get(
            reverse(self.url_follow_index))
        follow_index = response_follow_index.context['page_obj']

        self.assertIn(post, follow_index)

    def test_unfollow_correct_display_in_follow_index(self):
        """Новая запись пользователя не появляется
         в ленте тех, кто на него не подписан."""
        Post.objects.create(
            author=self.author,
            text='test-text',
        )
        posts = Post.objects.filter(
            author__following__user=self.non_author)

        response_follow_index = self.authorized_client_non_author.get(
            reverse(self.url_follow_index))
        follow_index = response_follow_index.context['page_obj']

        self.assertNotIn(posts, follow_index)


class PaginatorViewsTest(TestCase):
    TEST_OF_POST = settings.POSTS_PER_PAGE + 3

    def setUp(self):
        self.user = User.objects.create_user(username='Olga')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(title='test-group',
                                          slug='test-slug')
        test_post = []
        for posts in range(self.TEST_OF_POST):
            test_post.append(Post(
                text=f'test-text {posts}',
                group=self.group,
                author=self.user))
        Post.objects.bulk_create(test_post)

    def test_paginator(self):
        """На странице отображается 10 постов."""
        pages = (
            reverse('posts:index'),
            reverse('posts:group_posts', kwargs={
                'slug': self.group.slug}),
            reverse('posts:profile', kwargs={
                'username': self.user.username}),
        )

        for page in pages:
            response_first_page = self.authorized_client.get(page)
            response_second_page = self.authorized_client.get(page + '?page=2')
            count_posts_first_page = len(
                response_first_page.context['page_obj'])
            count_posts_second_page = len(
                response_second_page.context['page_obj'])
            final_count_posts = self.TEST_OF_POST - settings.POSTS_PER_PAGE

            self.assertEqual(
                count_posts_first_page, settings.POSTS_PER_PAGE)
            self.assertEqual(
                count_posts_second_page, final_count_posts)
