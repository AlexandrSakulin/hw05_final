from django.test import TestCase

from ..models import Group, Post, User


class PostsModelTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test-author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост тестового пользователя в тестовой группе',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        models = {
            self.group.title: self.group,
            self.post.text[:15]: self.post
        }
        for model_str, model in models.items():
            with self.subTest(model=model):
                self.assertEqual(model_str, model.__str__())

    def test_verbose_name_post(self):
        """Проверяем verbose_name в модели Post."""
        field_verbose = {
            'text': 'Пост',
            'pub_date': 'Дата',
            'author': 'Автор',
            'group': 'Группа'
        }
        for field, expected in field_verbose.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).verbose_name, expected)

    def test_verbose_name_group(self):
        """Проверяем verbose_name в модели Group."""
        field_verbose = {
            'title': 'Группа',
            'slug': 'Слаг группы',
            'description': 'Описание группы'
        }
        for field, expected in field_verbose.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.group._meta.get_field(field).verbose_name, expected)

    def test_help_text_post(self):
        """Проверяем help_text в модели Post."""
        field_help_text = {
            'text': 'Введите текст поста',
            'group': 'Выберите группу'
        }
        for field, expected in field_help_text.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).help_text, expected)

    def test_help_text_group(self):
        """Проверяем help_text в модели Group."""
        field_help_text = {
            'title': 'Выберите группу для поста',
            'description': 'Введите описание группы'
        }
        for field, expected in field_help_text.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.group._meta.get_field(field).help_text, expected)
