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
    word = models.ForeignKey(Word, on_delete=models.CASCADE)  # 假设存在一个名为Word的单词模型
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.word.word} - {self.timestamp}"
    


