from django.contrib import admin
from .models import Word, WordGroup, StudyRecord, Achievement,UserAchievement
admin.site.register(Word)
admin.site.register(WordGroup)
admin.site.register(StudyRecord)
admin.site.register(Achievement)
admin.site.register(UserAchievement)
