from django.forms import ModelForm

from .models import Comment, Post


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ('group', 'text', 'image',)
        labels = {
            'text': 'Текст поста',
            'group': 'Group',
        }
        help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост'
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        help_texts = {
            'text': 'Введите текст комментария'
        }
        labels = {
            'text': 'Комментарий'
        }
