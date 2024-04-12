from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Word, WordGroup, StudyRecord, UserAchievement, StudyProgress
from .views import add_achievements
from django.utils import timezone
from datetime import timedelta


class WordModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # 测试
        group = WordGroup.objects.create(name='Test Group')
        Word.objects.create(word='test', meaning='test meaning', group=group)

    def test_word_word_label(self):
        word = Word.objects.get(id=1)
        field_label = word._meta.get_field('word').verbose_name
        self.assertEqual(field_label, 'word')

    def test_word_meaning_label(self):
        word = Word.objects.get(id=1)
        field_label = word._meta.get_field('meaning').verbose_name
        self.assertEqual(field_label, 'meaning')

    def test_word_group_label(self):
        word = Word.objects.get(id=1)
        field_label = word._meta.get_field('group').verbose_name
        self.assertEqual(field_label, 'group')

    def test_word_str_method(self):
        word = Word.objects.get(id=1)
        self.assertEqual(str(word), 'test')


class StudyRecordModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        group = WordGroup.objects.create(name='Test Group')
        word = Word.objects.create(
            word='test', meaning='test meaning', group=group)
        user = User.objects.create_user(username='testuser', password='12345')
        StudyRecord.objects.create(
            user=user, word=word, timestamp=timezone.now())

    def test_study_record_user_label(self):
        record = StudyRecord.objects.get(id=1)
        field_label = record._meta.get_field('user').verbose_name
        self.assertEqual(field_label, 'user')

    def test_study_record_word_label(self):
        record = StudyRecord.objects.get(id=1)
        field_label = record._meta.get_field('word').verbose_name
        self.assertEqual(field_label, 'word')

    def test_study_record_timestamp_label(self):
        record = StudyRecord.objects.get(id=1)
        field_label = record._meta.get_field('timestamp').verbose_name
        self.assertEqual(field_label, 'timestamp')

    def test_study_record_str_method(self):
        record = StudyRecord.objects.get(id=1)
        self.assertEqual(
            str(record), 'testuser - test - {}'.format(record.timestamp))


class ViewTests(TestCase):
    @classmethod
    def setUpTestData(self):
        self.user = User.objects.create(username='test_user', password='12345')
        self.admin_user = User.objects.create_user(
            username='admin', password='adminpass', is_staff=True)
        group = WordGroup.objects.create(name='Test Group')
        Word.objects.create(word='test', meaning='test meaning', group=group)
        self.group = WordGroup.objects.create(name='Test Group2')
        self.word1 = Word.objects.create(
            word='test1', meaning='meaning1', group=group)
        self.word2 = Word.objects.create(
            word='test2', meaning='meaning2', group=group)
        self.login_url = reverse('login')

    def test_index_view(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wordapp/index.html')

    def test_upload_csv_view(self):
        # 测试未登录用户
        response = self.client.get(reverse('upload_csv'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/admin/login/?next=/upload_csv/')

    def test_upload_csv_view_user(self):
        # 测试普通用户
        self.client.force_login(self.user)
        response = self.client.get(reverse('upload_csv'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/admin/login/?next=/upload_csv/')

    def test_upload_csv_view_admin(self):
        # 测试管理员
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('upload_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wordapp/upload_csv.html')

    def test_display_words_view(self):
        response = self.client.get(reverse('display_words'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wordapp/display_words.html')
        self.assertIn(self.group, response.context['words_by_group'])

    def test_start_game_view(self):
        response = self.client.get(reverse('start_game'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wordapp/start_game.html')
        self.assertIn(self.group, response.context['groups'])

    def test_game_view_get(self):
        response = self.client.get(reverse('game', args=[self.group.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wordapp/game.html')
        self.assertIn('word', response.context)

    def test_game_view_post_correct_guess(self):
        response = self.client.post(reverse('game', args=[self.group.id]), {
                                    'word_id': self.word1.id, 'guess': 'test1'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wordapp/game.html')
        self.assertIn('success_message', response.context)

    def test_game_view_post_incorrect_guess(self):
        response = self.client.post(reverse('game', args=[self.group.id]), {
                                    'word_id': self.word1.id, 'guess': 'wrong'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wordapp/game.html')
        self.assertIn('error_message', response.context)

    def test_view_study_records_authenticated(self):
        # 测试登录用户查看学习记录页面是否正常
        self.client.force_login(self.user)
        response = self.client.get(reverse("view_study_records"))
        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response, 'wordapp/view_study_records.html')

    def test_view_study_records_unauthenticated(self):
        # 测试未登录用户查看学习记录页面是否重定向到登录页面
        response = self.client.get(reverse('view_study_records'))
        # 检查重定向
        self.assertRedirects(
            response, f'/login/?next={reverse("view_study_records")}')


class StudyAchievementTest(TestCase):
    @classmethod
    # 测试成就能否正常添加
    def setUpTestData(cls):
        group = WordGroup.objects.create(name='Test Group')
        user = User.objects.create_user(username='testuser', password='12345')
        Word.objects.create(word='test', meaning='test meaning', group=group)
        for i in range(1010):  # 创建测试用例
            today = timezone.now().date()
            word = Word.objects.create(
                word=i, meaning='test meaning'+str(i), group=group)
            StudyRecord.objects.create(
                user=user, timestamp=today - timedelta(days=i), word_id=word.id)
            # timestamp无法手动设置，只能自动添加，所以这是一天学1010个单词时候的情况

    def test_achievement(self):

        user = User.objects.get(username='testuser')
        user_id = user.id

        self.user = user
        add_achievements(user_id)
        self.assertTrue(UserAchievement.objects.filter(
            user=self.user, achievement__name="千里之行").exists())
        self.assertTrue(UserAchievement.objects.filter(
            user=self.user, achievement__name="拾级而上").exists())
        self.assertTrue(UserAchievement.objects.filter(
            user=self.user, achievement__name="积少成多").exists())
        self.assertTrue(UserAchievement.objects.filter(
            user=self.user, achievement__name="词汇大师").exists())
        self.assertTrue(UserAchievement.objects.filter(
            user=self.user, achievement__name="学富五车").exists())
        self.assertTrue(UserAchievement.objects.filter(
            user=self.user, achievement__name="博闻强识").exists())


class StudyProgressTestCase(TestCase):
    def setUp(self):
        # 创建一个用户
        self.user = User.objects.create(
            username='testuser', password='testpassword')

        # 创建两个单词组
        self.group1 = WordGroup.objects.create(name='Group 1')
        self.group2 = WordGroup.objects.create(name='Group 2')

    def test_create_multiple_study_progress(self):
        # 创建两个 StudyProgress 实例并与同一个用户关联
        progress1 = StudyProgress.objects.create(
            user=self.user, word_group=self.group1)
        progress2 = StudyProgress.objects.create(
            user=self.user, word_group=self.group2)
        self.assertIsNotNone(progress1)
        self.assertIsNotNone(progress2)
        self.assertEqual(progress1.user, self.user)
        self.assertEqual(progress2.user, self.user)
        self.assertEqual(progress1.word_group, self.group1)
        self.assertEqual(progress2.word_group, self.group2)
