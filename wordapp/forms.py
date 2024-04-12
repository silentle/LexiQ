from django import forms
from .models import WordGroup


class UploadCSVForm(forms.Form):
    csv_file = forms.FileField(label='选择 CSV 文件')

class WordGroupForm(forms.Form):#开始游戏时的表格
    group = forms.ModelChoiceField(
        queryset=WordGroup.objects.all(), empty_label=None)
