from django.db import models
from django.contrib.auth.models import User


class WordGroup(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Word(models.Model):
    word = models.CharField(max_length=100)
    meaning = models.CharField(max_length=255)
    group = models.ForeignKey(WordGroup, on_delete=models.CASCADE)  # 与单词组关联

    class Meta:
        app_label = 'wordapp'

    def __str__(self):
        return self.word


class StudyRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    word = models.ForeignKey(Word, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.word.word} - {self.timestamp}"


class StudyProgress(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    word_group = models.ForeignKey(WordGroup, on_delete=models.CASCADE)
    words_to_learn = models.ManyToManyField(
        Word, related_name='words_to_learn')

    def __str__(self):
        return f"{self.user.username} - {self.word_group.name} Progress"

    def create_progress(self):
        """
        创建学习进度，将单词组中的所有单词添加到学习进度中
        """
        words = Word.objects.filter(group=self.word_group)
        for word in words:
            self.words_to_learn.add(word)

    def remove_word(self, word):
        """
        从学习进度中删除单词
        """
        self.words_to_learn.remove(word)

    def reset_progress(self):
        """
        重置学习进度，将单词组中的所有单词重新添加到学习进度中
        """
        self.words_to_learn.clear()
        self.create_progress()


class Achievement(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name


class UserAchievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    achieved_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.achievement.name}"
