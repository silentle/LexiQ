from django.db import models


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

