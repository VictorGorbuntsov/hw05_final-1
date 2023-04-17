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
        self.authorized_client.post(
            reverse('posts:profile_follow', args=(self.user2.username,)),
            follow=True
        )
        self.assertEqual(len(Follow.objects.all()), 1)
        following = Follow.objects.first()
        self.assertEqual(following.author, self.user2)
        self.assertEqual(following.user, self.user)

    def test_auth_client_unfollow(self):
        "Тест, проверяющий отписку"
        following = Follow.objects.create(
            user=self.user,
            author=self.user2,
        )
        self.assertEqual(len(Follow.objects.all()), 1)
        self.authorized_client.post(
            reverse('posts:profile_unfollow',
                    args=(following.author.username,)),
            follow=True
        )
        self.assertEqual(len(Follow.objects.all()), 0)

    def test_auth_client_re_follow(self):
        """Тест повторной подписки"""
        self.assertEqual(len(Follow.objects.all()), 0)
        self.authorized_client.post(
            reverse('posts:profile_follow', args=(self.user2.username,)),
            follow=True
        )
        self.assertEqual(len(Follow.objects.all()), 1)
        self.authorized_client.post(
            reverse('posts:profile_follow', args=(self.user2.username,)),
            follow=True
        )
        self.assertEqual(len(Follow.objects.all()), 1)

    def test_follow_to_yourserf(self):
        self.assertEqual(len(Follow.objects.all()), 0)
        self.authorized_client.post(
            reverse('posts:profile_follow', args=(self.user.username,)),
            follow=True
        )
        self.assertEqual(len(Follow.objects.all()), 0)
