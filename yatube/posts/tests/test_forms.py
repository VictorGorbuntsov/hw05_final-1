from http import HTTPStatus
import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='75',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Какой-то текст',
            group=cls.group,
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        Post.objects.all().delete()
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
        group = self.group
        posts_count = Post.objects.count()
        self.assertEqual(posts_count, 0)
        form_data = {
            'text': 'Тестовый текст',
            'group': group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:profile',
                                               args=(self.user.username,)))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        post = Post.objects.first()
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.group.id, form_data["group"])
        self.assertEqual(post.text, form_data["text"])
        self.assertEqual(post.image, f'posts/{form_data["image"].name}')

    def test_edit_post(self):
        """Редактированный пост сохраняется в БД c post_id."""
        group2 = Group.objects.create(
            title='Новая группа',
            slug='new-group',
            description='описание' * 5,
        )
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='some.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'asdfsafd',
            'group': group2.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=(self.post.id,)),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail',
                    args=(self.post.id,)),
        )
        post = Post.objects.first()
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.image, 'posts/some.gif')
        response = self.client.get(reverse('posts:group_list',
                                           args=(self.group.slug,)))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.context['page_obj']), 0)
        self.assertEqual(post.id, self.post.id)
        self.assertEqual(Post.objects.count(), posts_count)

    def test_guest_create_post(self):
        """Не залогиненный пользователь не может создавать посты."""
        Post.objects.all().delete()
        posts_count = Post.objects.count()
        self.assertEqual(posts_count, 0)
        form_data = {
            'text': 'asdfsafd',
            'group': self.group.id,
        }
        response = self.client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), posts_count)
