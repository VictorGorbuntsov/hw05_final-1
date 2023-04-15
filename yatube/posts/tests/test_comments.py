from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from ..forms import CommentForm
from ..models import Post, User


class CommentCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст жи есть',
        )
        cls.form = CommentForm()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_auth_client_comment(self):
        """Тест, комментировать пост может авторизованный клиент"""
        form_data = {
            'text': 'post is good!'
        }
        count_comments = len(self.post.comments.all())
        response = self.authorized_client.post(
            reverse('posts:add_comment', args=(self.post.id,)),
            data=form_data,
            follow=True,
        )
        self.assertEqual(len(self.post.comments.all()), count_comments + 1)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.authorized_client.get(
            reverse('posts:post_detail', args=(self.post.id,)),
            follow=True,
        )
        self.assertEqual(len(response.context.get('comments')), 1)
        comment = response.context.get('comments')[0]
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.post, self.post)
        self.assertEqual(comment.text, form_data['text'])

    def test_guest_client_comment(self):
        """Тест, комментировать пост не может аноним клиент"""
        form_data = {
            'text': 'post is good!'
        }
        count_comments = len(self.post.comments.all())
        response = self.client.post(
            reverse('posts:add_comment', args=(self.post.id,)),
            data=form_data,
            follow=True,
        )
        self.assertEqual(len(self.post.comments.all()), count_comments)
        self.assertEqual(response.status_code, HTTPStatus.OK)
