from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Follow, Post, User


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user2 = User.objects.create_user(username='auth2')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый тексt',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_auth_client_follow(self):
        """Тест проверяющий то, что авторизованный пользователь может
        подписываться на других и удалять их из подписок"""
        self.assertEqual(len(Follow.objects.all()), 0)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 0)
        response = self.authorized_client.post(
            reverse('posts:profile_follow', args=(self.user2.username,)),
            follow=True
        )
        self.assertEqual(len(Follow.objects.all()), 1)
