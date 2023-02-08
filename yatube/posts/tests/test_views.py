from django import forms
from django.conf import settings
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import PostForm
from ..models import Follow, Group, Post, User

TEST_POST_TEXT = 'Тестовый пост №13 тестового пользователя в тестовой группе'
ZERO = 0
ONE = 1


class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.author = User.objects.get(username='test_user')
        cls.follower = User.objects.create_user(username='follower')
        cls.following = User.objects.create_user(username='following')
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
            text=TEST_POST_TEXT,
        )

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.force_login(PostsViewsTests.user)
        self.auth_author = Client()
        self.auth_author.force_login(self.author)
        self.auth_follower_client = Client()
        self.auth_follower_client.force_login(self.follower)
        self.auth_following_client = Client()
        self.auth_following_client.force_login(self.following)

    def function_check(self, response, boolean=False):
        if boolean:
            post = response.context.get('post')
        else:
            post = response.context['page_obj'][0]
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.pub_date, self.post.pub_date)
        self.assertEqual(post.image, self.post.image)

    def test_index_pages_show_correct_context(self):
        """Проверка контекста в index"""
        response = self.auth_client.get(reverse('posts:index'))
        self.function_check(response)

    def test_group_list_pages_show_correct_context(self):
        """Проверка контекста в group_list"""
        response = self.auth_client.get(reverse(
            'posts:group_list', args=(self.group.slug,))
        )
        self.function_check(response)
        group_context = response.context['group']
        self.assertEqual(group_context, self.group)

    def test_profile_pages_show_correct_context(self):
        """Проверка контекста в profile"""
        response = self.auth_client.get(reverse(
            'posts:profile', args=(self.user.username,))
        )
        self.function_check(response)
        group_context = response.context['author']
        self.assertEqual(group_context, self.user)

    def test_post_detail_pages_show_correct_context(self):
        """Проверка контекста в post_detail"""
        response = self.auth_client.get(reverse(
            'posts:post_detail', args=(self.post.id,))
        )
        self.function_check(response, True)

    def test_post_create_and_edit_show_correct_context(self):
        """Шаблон create_post (create) and (edit) сформирован
        с правильным контекстом."""
        context_urls = (
            ('posts:post_create', None),
            ('posts:post_edit', (self.post.id,))
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for address, args in context_urls:
            with self.subTest(address=address):
                response = self.auth_client.get(
                    reverse(address, args=args)
                )
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context.get('form'), PostForm)
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = response.context.get('form').fields.get(
                            value
                        )
                        self.assertIsInstance(form_field, expected)

    def test_post_correct_not_appear(self):
        """Проверка, что созданный пост не появляется в группе """
        """к которой он не принадлежит."""

        post_count = Post.objects.count()
        post2 = Post.objects.create(
            author=self.user,
            text='Тестовый пост 2',
            group=self.group
        )
        group3 = Group.objects.create(
            title='Новая группа',
            slug='new-slug',
            description='Новое описание',
        )
        response1 = self.auth_client.get(reverse(
            'posts:group_list', args=(group3.slug,))
        )
        response2 = self.auth_client.get(reverse(
            'posts:group_list', args=(self.group.slug,))
        )
        self.assertEqual(len(response1.context['page_obj']), ZERO)
        self.assertEqual(post2.group, self.group)
        self.assertEqual(len(response2.context['page_obj']), post_count + ONE)

    def test_cache_index(self):
        """Проверяем что главная отдает кэшированные данные."""
        response_1 = self.auth_client.get(reverse('posts:index'))
        Post.objects.all().delete()
        response_2 = self.auth_client.get(reverse('posts:index'))
        self.assertTrue(response_1.content == response_2.content)
        cache.clear()
        response_3 = self.auth_client.get(reverse('posts:index'))
        self.assertTrue(response_1.content != response_3.content)

    def test_follow(self):
        """Авторизованный пользователь может подписываться"""
        follow_count = Follow.objects.count()
        self.auth_follower_client.get(
            reverse(
                'posts:profile_follow',
                args=(self.following,)
            )
        )
        follow_count2 = Follow.objects.count()
        self.assertEqual(follow_count + 1, follow_count2)

    def test_unfollow(self):
        """Авторизованный пользователь может ОТписываться"""
        Follow.objects.create(user=self.follower, author=self.following)
        follow_count = Follow.objects.count()
        self.auth_follower_client.get(
            reverse(
                'posts:profile_unfollow',
                args=(self.following,)
            )
        )
        follow_count2 = Follow.objects.count()
        self.assertEqual(follow_count - 1, follow_count2)

    def test_post_follow(self):
        """Новая запись follow у подписчика"""
        Follow.objects.create(user=self.user, author=self.author)
        response = self.auth_author.get(
            reverse('posts:follow_index')
        )
        self.assertIn(self.post, response.context['page_obj'])

    def test_unfollow_not_post(self):
        """Нового поста нет, кто не подписан"""
        response = self.auth_client.get(
            reverse('posts:follow_index')
        )
        content = response.context['page_obj']
        self.assertNotIn(self.post, content)

    def test_follow_self(self):
        """Тестирование подписки на самого себя"""
        follow_count = Follow.objects.count()
        self.auth_follower_client.get(
            reverse(
                'posts:profile_follow',
                args=(self.follower,)
            )
        )
        follow_count2 = Follow.objects.count()
        self.assertEqual(follow_count, follow_count2)

    def test_return_follow_self(self):
        """Тестирование повторной подписки"""
        follow_count = Follow.objects.count()
        self.auth_follower_client.get(
            reverse(
                'posts:profile_follow',
                args=(self.following,)
            )
        )
        follow_count2 = Follow.objects.count()
        self.assertEqual(follow_count + 1, follow_count2)
        self.auth_follower_client.get(
            reverse(
                'posts:profile_follow',
                args=(self.following,)
            )
        )
        follow_count3 = Follow.objects.count()
        self.assertEqual(follow_count2, follow_count3)


class PaginatorViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='test-author')
        cls.user_2 = User.objects.create_user(username='follower')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user_2)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Описание тестовой группы'
        )
        post_list = []
        for posts in range(settings.THIRTEEN):
            new_post = Post(
                text=f'Тестовый пост контент {posts}',
                group=cls.group,
                author=cls.user
            )
            post_list.append(new_post)
        Post.objects.bulk_create(post_list)

    def setUp(self):
        Follow.objects.create(user=self.user_2, author=self.user)

    def test_paginator(self):
        """Проверка пагинатора"""
        paginator_urls = (
            ('posts:index', None),
            ('posts:group_list', (self.group.slug,)),
            ('posts:profile', (self.user.username,)),
            ('posts:follow_index', None)
        )
        pages_units = (
            ('?page=1', settings.POSTS_IN_PAGE),
            ('?page=2', settings.THIRTEEN - settings.POSTS_IN_PAGE)
        )

        for address, args in paginator_urls:
            with self.subTest(address=address):
                for page, units in pages_units:
                    with self.subTest(page=page):
                        response = self.auth_client.get(
                            reverse(address, args=args) + page
                        )
                        self.assertEqual(
                            len(response.context['page_obj']), units
                        )
