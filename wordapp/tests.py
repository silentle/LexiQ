from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Word, WordGroup, StudyRecord,UserAchievement
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
    def setUpTestData(cls):
        group = WordGroup.objects.create(name='Test Group')
        Word.objects.create(word='test', meaning='test meaning', group=group)

    def test_start_game_view(self):
        response = self.client.get(reverse('start_game'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wordapp/start_game.html')

    def test_game_view(self):
        response = self.client.get(reverse('game', kwargs={'group_id': 1}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wordapp/game.html')
        
class StudyAchievementTest(TestCase):
    @classmethod
    #测试成就能否正常添加
    def setUpTestData(cls):
        group = WordGroup.objects.create(name='Test Group')
        user = User.objects.create_user(username='testuser', password='12345')
        userid=user.id
        Word.objects.create(word='test', meaning='test meaning', group=group)
        for i in range(1010):#创建测试用例
            today = timezone.now().date()
            word=Word.objects.create(word=i, meaning='test meaning'+str(i), group=group)
            StudyRecord.objects.create(user=user, timestamp=today - timedelta(days=i),word_id=word.id)
            #timestamp无法手动设置，只能自动添加，所以这是一天学1010个单词时候的情况
        

    def test_achievement(self):

        user = User.objects.get(username='testuser')
        user_id=user.id

        self.user=user
        add_achievements(user_id)
        self.assertTrue(UserAchievement.objects.filter(user=self.user, achievement__name="千里之行").exists())
        self.assertTrue(UserAchievement.objects.filter(user=self.user, achievement__name="拾级而上").exists())
        self.assertTrue(UserAchievement.objects.filter(user=self.user, achievement__name="积少成多").exists())
        self.assertTrue(UserAchievement.objects.filter(user=self.user, achievement__name="词汇大师").exists())
        self.assertTrue(UserAchievement.objects.filter(user=self.user, achievement__name="学富五车").exists())
        self.assertTrue(UserAchievement.objects.filter(user=self.user, achievement__name="博闻强识").exists())


