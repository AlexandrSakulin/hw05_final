from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test-author')
        cls.author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост достаточной длины',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)
        self.urls_template = (
            ('posts:index', None),
            ('posts:group_list', (self.group.slug,)),
            ('posts:profile', (self.author,)),
            ('posts:post_detail', (self.post.id,)),
            ('posts:post_create', None),
            ('posts:post_edit', (self.post.id,)),
            ('posts:add_comment', (self.post.id,)),
            ('posts:follow_index', None),
            ('posts:profile_follow', (self.author,)),
            ('posts:profile_unfollow', (self.author,)),
        )

    def test_guest_access(self):
        """Доступность для гостя."""
        for address, args in self.urls_template:
            with self.subTest(address=address):
                reverse_list = [
                    'posts:post_create',
                    'posts:post_edit',
                    'posts:add_comment',
                    'posts:follow_index',
                    'posts:profile_follow',
                    'posts:profile_unfollow'
                ]
                if address in reverse_list:
                    response = self.client.get(
                        reverse(address, args=args), follow=True
                    )
                    reverse_login = reverse('users:login')
                    reverse_name = reverse(address, args=args)
                    self.assertRedirects(
                        response, f'{reverse_login}?next={reverse_name}'
                    )
                else:
                    response = self.client.get(reverse(address, args=args))
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_user_access(self):
        """Доступность для пользователя."""
        for address, args in self.urls_template:
            with self.subTest(address=address):
                response = self.authorized_client.get(
                    reverse(address, args=args)
                )
                if address == 'posts:post_edit':
                    self.assertRedirects(
                        response, reverse(
                            'posts:post_detail', args=(self.post.id,))
                    )
                elif address in [
                    'posts:add_comment',
                ]:
                    self.assertRedirects(response, reverse(
                        'posts:post_detail', args=(self.post.id,))
                    )
                elif address in [
                    'posts:profile_follow',
                    'posts:profile_unfollow'
                ]:
                    self.assertRedirects(response, reverse(
                        'posts:profile', args=(self.author,))
                    )
                else:
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_author_access(self):
        """Доступность для автора."""
        for address, args in self.urls_template:
            with self.subTest(address=address):
                response = self.authorized_author.get(
                    reverse(address, args=args)
                )
                if address in [
                    'posts:add_comment',
                ]:
                    self.assertRedirects(response, reverse(
                        'posts:post_detail', args=(self.post.id,))
                    )
                elif address in [
                    'posts:profile_follow',
                ]:
                    self.assertRedirects(response, reverse(
                        'posts:profile', args=(self.author,))
                    )
                elif address in [
                    'posts:profile_unfollow'
                ]:
                    self.assertEqual(response.status_code,
                                     HTTPStatus.NOT_FOUND)
                else:
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_guest_fakepage(self):
        """Ответ 404 на несуществующую страницу"""
        response = self.client.get('/fakepage/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_correct_templates(self):
        """Проверка корректности шаблонов"""
        templates_urls = (
            ('posts:index', None, 'posts/index.html'),
            ('posts:group_list', (self.group.slug,), 'posts/group_list.html'),
            ('posts:profile', (self.author,), 'posts/profile.html'),
            ('posts:post_detail', (self.post.id,), 'posts/post_detail.html'),
            ('posts:post_create', None, 'posts/create_post.html'),
            ('posts:post_edit', (self.post.id,), 'posts/create_post.html'),
            ('posts:follow_index', None, 'posts/follow.html')
        )
        for address, args, template in templates_urls:
            with self.subTest(address=address):
                response = self.authorized_author.get(
                    reverse(address, args=args)
                )
                self.assertTemplateUsed(response, template)

    def test_reverse_urls_correct(self):
        """Корректность реверса"""
        reverse_urls = (
            ('posts:index', None, '/'),
            ('posts:group_list', (self.group.slug,), (f'/group/'
                                                      f'{self.group.slug}/')),
            ('posts:profile', (self.author,), f'/profile/{self.author}/'),
            ('posts:post_detail', (self.post.id,), f'/posts/{self.post.id}/'),
            ('posts:post_create', None, '/create/'),
            ('posts:post_edit', (self.post.id,), f'/posts/'
                                                 f'{self.post.id}/edit/'),
            ('posts:add_comment', (self.post.id,), f'/posts/'
                                                   f'{self.post.id}/comment/'),
            ('posts:follow_index', None, '/follow/'),
            ('posts:profile_follow', (self.author,), f'/profile/'
                                                     f'{self.author}/follow/'),
            ('posts:profile_unfollow', (self.author,), f'/profile/'
                                                       f'{self.author}/'
                                                       f'unfollow/'),
        )
        for address, args, links in reverse_urls:
            with self.subTest(address=address):
                self.assertEqual(reverse(address, args=args), links)
