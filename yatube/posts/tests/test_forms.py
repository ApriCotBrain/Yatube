import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import CommentForm, PostForm
from posts.models import Comment, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = Post.objects.create(
            author=User.objects.create_user(username='Olga'),
            text='test-post',
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.post.author)

    def test_create_post(self):
        """Отправка валидной формы создает запись."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'test-post',
            'image': uploaded,
        }

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertRedirects(
            response,
            reverse('posts:profile',
                    kwargs={'username': self.post.author}))
        self.assertTrue(Post.objects.filter(
            text=self.post.text,
            author=self.post.author,
            group=self.post.group,
            image=self.post.image).exists())
        self.assertEqual(Post.objects.count(), posts_count + 1)

    def test_edit_post(self):
        """При отправке валидной формы происходит изменение поста."""
        old_post = Post.objects.create(
            text='test-post',
            author=self.post.author,
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'test-update-post',
            'image': uploaded,
        }
        posts_count = Post.objects.count()

        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': old_post.id}),
            data=form_data,
            follow=True
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(Post.objects.filter(
            text=self.post.text,
            author=self.post.author,
            group=self.post.group,
            image=self.post.image).exists())

    def test_guest_client_create_post(self):
        """Неавторизованный пользователь
         не может создавать посты."""
        response = self.guest_client.post(
            reverse('posts:post_create')
        )

        self.assertRedirects(response, '/auth/login/?next=/create/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)


class CommentCreateFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = Post.objects.create(
            author=User.objects.create_user(username='Andrei'),
            text='test-post',
        )
        cls.comment = Comment.objects.create(
            author_id=1,
            text='test-comment',
            post=cls.post,
        )
        cls.form = CommentForm()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.comment.author)

    def test_add_comment(self):
        """Отправка валидной формы создает комментарий."""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'test-post',
        }

        response = self.authorized_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )

        self.assertRedirects(
            response,
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id}))
        self.assertTrue(Comment.objects.filter(
            text=self.comment.text,
            author=self.comment.author,
            post=self.post).exists())
        self.assertEqual(Comment.objects.count(), comments_count + 1)

    def test_add_comment_guest_client(self):
        """Комментировать посты может
         только авторизованный пользователь"""
        comments_count = Comment.objects.count()
        response = self.guest_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.id}),
            follow=True
        )
        redirect = f'/auth/login/?next=/posts/{self.post.id}/comment/'

        self.assertRedirects(response, redirect)
        self.assertEqual(Comment.objects.count(), comments_count)
