import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test-author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug2',
            description='Тестовое описание 2',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост',
        )

    def setUp(self):
        """Создаем клиента и пост."""
        self.auth_client = Client()
        self.auth_client.force_login(self.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post_form(self):
        """При отправке формы создается новый пост в базе данных.
        После создания происходит редирект на профиль автора.
        """
        Post.objects.all().delete()
        post_count = Post.objects.all().count()
        form_data = {
            'text': 'Тестовый пост',
            'group': self.group.id
        }
        response = self.auth_client.post(
            reverse('posts:post_create'),
            data=form_data,
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', args=(self.user.username,))
        )
        self.assertEqual(
            Post.objects.all().count(),
            post_count + 1,
            'Пост не сохранен в базу данных!'
        )
        post = Post.objects.first()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.user)
        self.assertEqual(form_data['group'], self.group.id)

    def test_authorized_user_edit_post(self):
        """Проверка редактирования записи авторизированным клиентом."""
        self.assertEqual(Post.objects.all().count(), 1)
        picture = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='picture.jpg',
            content=picture,
            content_type='image/picture'
        )
        form_data = {
            'text': 'Отредактированный текст поста',
            'group': self.group2.id,
            'image': uploaded,

        }
        response = self.auth_client.post(
            reverse(
                'posts:post_edit',
                args=(self.post.id,)),
            data=form_data,
            follow=True
        )
        old_groupe = self.auth_client.get(
            reverse('posts:group_list', args=(self.group.slug,)))
        self.assertRedirects(
            response,
            reverse('posts:post_detail', args=(self.post.pk,)))
        post = Post.objects.first()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.group_id, form_data['group'])
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(self.group.posts.count(), 0)
        self.assertEqual(self.group2.posts.count(), 1)
        self.assertTrue(
            old_groupe.context['page_obj'].paginator.count == 0
        )
        self.assertEqual(old_groupe.status_code, HTTPStatus.OK)
        self.assertTrue(
            Post.objects.filter(
                group=form_data['group'],
                text=form_data['text'],
                image='posts/picture.jpg'
            ).exists()
        )

    def test_guest_create_post(self):
        """Проверка что неавторизованный юзер
            не сможет создать пост."""

        post_count = Post.objects.count()
        form_fields = {
            'text': 'Тестовый пост контент 2',
            'group': self.group.pk
        }
        response = self.client.post(
            reverse('posts:post_create'),
            data=form_fields,
        )
        redirect = "%s?next=%s" % (
            reverse('users:login'), reverse('posts:post_create')
        )
        self.assertRedirects(response, redirect)
        self.assertEqual(Post.objects.count(), post_count)


class CommentFormsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test-author')
        cls.group = Group.objects.create(
            title='Тестовое название',
            description='Тестовое описание',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовая пост',
            group=cls.group,
        )

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)

    def test_comment_form_for_auth(self):
        """Комментарии только для авторизованных"""
        comm_count = self.post.comments.count()
        form_data = {
            'text': 'Новый комментарий',
            'author': self.author
        }
        response = self.client.post(
            reverse('posts:add_comment', args=(self.post.id,)),
            data=form_data,
            follow=True,
        )
        rev_login = reverse('users:login')
        rev_add_comment = reverse('posts:add_comment', args=(self.post.id,))
        redirect = f'{rev_login}?next={rev_add_comment}'
        self.assertRedirects(response, redirect)
        self.assertEqual(self.post.comments.count(), comm_count)

        response = self.authorized_author.post(
            reverse('posts:add_comment', args=(self.post.id,)),
            data=form_data,
            follow=True,
        )
        self.assertEqual(self.post.comments.count(), comm_count + 1)
        last_comm = self.post.comments.last()
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(last_comm.text, form_data['text'])
        self.assertEqual(last_comm.author, form_data['author'])
