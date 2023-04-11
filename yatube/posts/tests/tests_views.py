import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms

from ..models import Post, Group, User
from posts.forms import PostForm
from yatube.settings import NUMBER_OF_POSTS_IN_PAG

TOTAL_NUMBER_OF_POSTS = 13

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='75',
            description='Тестовое описание',
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
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='test*100',
            image=uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def check_post(self, response, is_post=False):
        if is_post:
            post = response.context['post']
        else:
            post = response.context['page_obj'][0]
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.group, self.post.group)
        self.assertEqual(post.pub_date, self.post.pub_date)
        self.assertTrue(post.image)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.client.get(reverse('posts:index'))
        self.check_post(response)

    def test_group_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.client.get(
            reverse('posts:group_list', args=(self.group.slug,)))
        self.assertIn('group', response.context)
        group = response.context.get('group')
        self.assertEqual(group, self.group)
        self.check_post(response)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.client.get(
            reverse('posts:profile', args=(self.user.username,)))
        self.assertIn('author', response.context)
        author = response.context.get('author')
        self.assertEqual(author, self.user)
        self.check_post(response)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.client.get(
            reverse('posts:post_detail', args=(self.post.id,)))
        self.check_post(response, is_post=True)

    def test_create_forms_value(self):
        """Проверка формы."""
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        urls = (
            ('posts:post_create', None),
            ('posts:post_edit', (self.post.id,)),
        )
        for url, slug in urls:
            reverse_name = reverse(url, args=slug)
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], PostForm)
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = response.context.get(
                            'form').fields.get(value)
                        self.assertIsInstance(form_field, expected)

    def test_post_in_wrong_group(self):
        """Проверка, что пост не попал в неправильную группу"""
        new_group = Group.objects.create(
            title='Новая группа',
            slug='new-group',
            description='Новое описание',
        )
        response = self.client.get(reverse('posts:group_list',
                                           args=(new_group.slug,)))
        self.assertEqual(len(response.context['page_obj']), 0)
        post = Post.objects.first()
        self.assertEqual(post.group, self.group)
        response = self.client.get(reverse('posts:group_list',
                                           args=(self.group.slug,)))
        self.assertIn(self.post, response.context['page_obj'])


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='75',
            description='Тестовое описание',
        )
        cls.posts = Post.objects.bulk_create(
            [Post(author=cls.user,
                  text=f'{index}',
                  group=cls.group) for index in range(TOTAL_NUMBER_OF_POSTS)]
        )
        cache.clear()

    def test_page(self):
        reverse_names = (
            ('posts:index', None),
            ('posts:group_list', (self.group.slug,)),
            ('posts:profile', (self.user.username,)),
        )
        posts_in_page = (
            ('?page=1', NUMBER_OF_POSTS_IN_PAG),
            ('?page=2', TOTAL_NUMBER_OF_POSTS - NUMBER_OF_POSTS_IN_PAG),
        )
        for name, args in reverse_names:
            with self.subTest(name=name):
                for page, number in posts_in_page:
                    with self.subTest(page=page):
                        response = self.client.get(reverse(name,
                                                           args=args) + page)
                        self.assertEqual(len(response.context['page_obj']),
                                         number)


class CacheViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='auth')
        self.post = Post.objects.create(
            author=self.user,
            text='This is a test post'
        )
        self.url = reverse('posts:index')
        cache.clear()

    def test_cache(self):
        response = self.client.get(self.url)
        self.assertIn(self.post.text.encode(), response.content)
        self.post.delete()
        response = self.client.get(self.url)
        self.assertIn(self.post.text.encode(), response.content)
        cache.clear()
        response = self.client.get(self.url)
        self.assertNotIn(self.post.text.encode(), response.content)
