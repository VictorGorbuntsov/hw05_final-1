from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ("text", "group", "image")
        labels = {
            'text': 'Текст поста',
            'group': 'Группа',
            'image': 'Картинка',
        }
        help_texts = {
            'text': 'Введите текст поста',
            'group': 'Выберите группу, к которой будет относиться пост',
            'image': 'Загрузите картинку к посту',
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("text",)
        labels = {
            'text': 'Комментарий'
        }
        help_texts = {
            'text': 'Напишите свой комментарий к посту',
        }
