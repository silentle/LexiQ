from django.shortcuts import render, redirect
from .models import Word, WordGroup, StudyRecord, StudyProgress, Achievement, User, UserAchievement
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
import csv
import random
import edge_tts
import os
from io import TextIOWrapper
from .forms import UploadCSVForm, WordGroupForm
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import login as auth_login
from datetime import timedelta
from django.utils import timezone


def index(request):
    return render(request, 'wordapp/index.html')


@staff_member_required
def upload_csv(request):
    if request.method == 'POST':
        form = UploadCSVForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            if not csv_file.name.endswith('.csv'):
                messages.error(request, '只能上传CSV文件')
                return redirect('upload_csv')

            group_name = csv_file.name.replace('.csv', '')  # 使用文件名作为单词组名
            group, created = WordGroup.objects.get_or_create(name=group_name)

            # 使用 TextIOWrapper 将文件转换为文本文件
            csv_text = TextIOWrapper(csv_file.file, encoding='utf-8')
            reader = csv.reader(csv_text)
            for row in reader:
                word, meaning = row
                Word.objects.create(word=word, meaning=meaning, group=group)

            messages.success(request, 'CSV 文件上传成功.')
            return redirect('upload_csv')
    else:
        form = UploadCSVForm()

    groups = WordGroup.objects.all()
    return render(request, 'wordapp/upload_csv.html', {'form': form, 'groups': groups})


@staff_member_required
def delete_word_group(request, group_id):
    if request.method == 'POST':
        Word.objects.filter(group_id=group_id).delete()
        WordGroup.objects.filter(id=group_id).delete()
        messages.success(request, '单词组删除成功')
        return redirect('upload_csv')
    return redirect('upload_csv')


def display_words(request):
    groups = WordGroup.objects.all()  # 获取所有单词分组
    words_by_group = {}
    for group in groups:
        # 获取每个分组下的单词列表，ord.objects.filter(group=group) 使用Word模型的objects管理器的filter方法过滤group字段等于当前循环的group的值
        words_by_group[group] = Word.objects.filter(group=group)
    return render(request, 'wordapp/display_words.html', {'words_by_group': words_by_group})


def start_game(request):
    if request.method == 'POST':
        form = WordGroupForm(request.POST)
        if form.is_valid():
            selected_group = form.cleaned_data['group']
            return redirect('game', group_id=selected_group.id)
    else:
        form = WordGroupForm()
    groups = WordGroup.objects.all()
    return render(request, 'wordapp/start_game.html', {'form': form, 'groups': groups})


def game(request, group_id):
    last_guess = request.POST.get('guess', '')  # 获取上次提交的猜测值，如果没有则为空字符串

    if request.method == 'POST':
        word_id = request.POST.get('word_id')
        guessed_word = request.POST.get('guess')
        word = Word.objects.get(pk=word_id)

        # 检查用户的猜测是否完全正确
        if all(g == a for g, a in zip(guessed_word, word.word)):
            # 如果猜测正确，自动切换到下一个单词
            words = Word.objects.filter(group_id=group_id)
            if words.exists():
                if request.user.is_authenticated:
                    study_record = StudyRecord(user=request.user, word=word)
                    study_record.save()
                # 如果用户已登录，从学习进度中获取下一个单词
                if request.user.is_authenticated:
                    study_progress = StudyProgress.objects.get_or_create(
                        user=request.user, word_group_id=group_id)
                    if study_progress.words_to_learn.exists():
                        word = study_progress.words_to_learn.first()
                        study_progress.remove_word(word)
                    else:
                        # 如果学习进度中的单词已全部学完，则重置学习进度
                        study_progress.reset_progress()
                        word = study_progress.words_to_learn.first()
                else:
                    word = random.choice(words)

                context = {
                    'word': word,
                    'success_message': '恭喜，猜对了'
                }
                return render(request, 'wordapp/game.html', context)
            else:
                return redirect('start_game')
        else:
            # 如果猜测不正确，显示反馈但保持在当前单词页面
            feedback = get_feedback(word.word, guessed_word)
            combined_list = zip(feedback, guessed_word)
            context = {
                'word': word,
                'feedback': feedback,
                'guessed_word': guessed_word,
                'combined_list': combined_list,
                'error_message': '猜错了，请重试',
                'last_guess': last_guess
            }
            return render(request, 'wordapp/game.html', context)
    else:
        words = Word.objects.filter(group_id=group_id)
        if words.exists():
            if request.user.is_authenticated:
                study_progress = StudyProgress.objects.get_or_create(
                    user=request.user, word_group_id=group_id)
                if study_progress.words_to_learn.exists():
                    word = study_progress.words_to_learn.first()
                    study_progress.remove_word(word)
                else:
                    study_progress.reset_progress()
                    word = study_progress.words_to_learn.first()
            else:
                word = random.choice(words)

            context = {
                'word': word,
            }
            return render(request, 'wordapp/game.html', context)
        else:
            return redirect('start_game')


def get_feedback(actual_word, guessed_word):
    feedback = []
    # 确保猜测的单词长度与实际单词的长度相同
    guessed_word = guessed_word.ljust(len(actual_word), ' ')  # 使用空格填充短的猜测单词
    for i in range(len(actual_word)):
        if guessed_word[i] == actual_word[i]:
            feedback.append('green')  # 绿色表示字母和位置都正确
        elif guessed_word[i] in actual_word:
            feedback.append('yellow')  # 黄色表示字母正确但位置不正确
        else:
            feedback.append('gray')  # 灰色表示字母不在答案中
    return feedback


async def tts(request, word):  # 异步
    delete_files_in_folder('wordapp/tts')
    TEXT = word
    VOICE = "en-GB-SoniaNeural"
    OUTPUT_FILE = f"wordapp/tts/{word}.mp3"

    communicate = edge_tts.Communicate(TEXT, VOICE)
    await communicate.save(OUTPUT_FILE)

    return JsonResponse({'status': 'success', 'filename': OUTPUT_FILE})


def delete_files_in_folder(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error deleting file: {e}")


def play_audio(request, file_path):
    # 构造音频文件的完整路径
    audio_file = file_path
    # 以二进制形式打开音频文件
    with open(audio_file, 'rb') as f:
        response = HttpResponse(f.read(), content_type="audio/mp3")
        return response


def login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect('start_game')  # 登录成功后重定向到开始界面
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  # 注册成功后重定向到登录页面
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


def view_study_records(request):
    # 如果用户已登录，则查询该用户的学习记录并按时间排序
    if request.user.is_authenticated:
        current_user = request.user
        study_records = StudyRecord.objects.filter(user=current_user).order_by('-timestamp')
        total_records = study_records.count()
        
        # 检查并添加成就
        user_id = current_user.id
        add_achievements(user_id)
        
        # 获取用户的成就
        user_achievements = UserAchievement.objects.filter(user=current_user)
        
        return render(request, 'wordapp/view_study_records.html', {'study_records': study_records, 'total_records': total_records, 'user_achievements': user_achievements})
    else:
        # 如果用户未登录，重定向到登录页面
        return render(request, 'registration/login.html')



def add_achievements(user_id):
    user = User.objects.get(pk=user_id)
    study_records = StudyRecord.objects.filter(
        user=user).order_by('-timestamp')
    total_records = study_records.count()

    # 千里之行
    if total_records >= 1:
        if not UserAchievement.objects.filter(user=user, achievement__name="千里之行").exists():
            achievement = Achievement.objects.create(
                name="千里之行", description="学习第一个单词")
            UserAchievement.objects.create(user=user, achievement=achievement)

    # 拾级而上
    if total_records >= 10:
        if not UserAchievement.objects.filter(user=user, achievement__name="拾级而上").exists():
            achievement = Achievement.objects.create(
                name="拾级而上", description="学习10个单词")
            UserAchievement.objects.create(user=user, achievement=achievement)

    # 积少成多
    if total_records >= 100:
        if not UserAchievement.objects.filter(user=user, achievement__name="积少成多").exists():
            achievement = Achievement.objects.create(
                name="积少成多", description="学习100个单词")
            UserAchievement.objects.create(user=user, achievement=achievement)

    # 登堂入室
    if total_records >= 500:
        if not UserAchievement.objects.filter(user=user, achievement__name="词汇大师").exists():
            achievement = Achievement.objects.create(
                name="词汇大师", description="学习500个单词")
            UserAchievement.objects.create(user=user, achievement=achievement)

    # 学富五车
    if total_records >= 1000:
        if not UserAchievement.objects.filter(user=user, achievement__name="学富五车").exists():
            achievement = Achievement.objects.create(
                name="学富五车", description="学习1000个单词")
            UserAchievement.objects.create(user=user, achievement=achievement)
    # 心如明镜
    if check_consecutive_days(study_records, 30):
        if not UserAchievement.objects.filter(user=user, achievement__name="心如明镜").exists():
            achievement = Achievement.objects.create(
                name="心如明镜", description="连续学习30天")
            UserAchievement.objects.create(user=user, achievement=achievement)

    # 清风明月
    if check_consecutive_days(study_records, 60):
        if not UserAchievement.objects.filter(user=user, achievement__name="清风明月").exists():
            achievement = Achievement.objects.create(
                name="清风明月", description="连续学习60天")
            UserAchievement.objects.create(user=user, achievement=achievement)

    # 博闻强识
    if check_words_in_week(study_records, 50):
        if not UserAchievement.objects.filter(user=user, achievement__name="博闻强识").exists():
            achievement = Achievement.objects.create(
                name="博闻强识", description="在一周内学50个单词")
            UserAchievement.objects.create(user=user, achievement=achievement)


def check_consecutive_days(study_records, days):
    today = timezone.now().date()
    start_date = today - timedelta(days=days-1)
    consecutive_days = 0
    for record in study_records:
        if record.timestamp.date() >= start_date and record.timestamp.date() <= today:
            consecutive_days += 1
            if consecutive_days == days:
                return True
        else:
            consecutive_days = 0
    return False


def check_words_in_week(study_records, count):
    today = timezone.now().date()
    start_date = today - timedelta(days=7)
    words_in_week = 0
    for record in study_records:
        if record.timestamp.date() >= start_date and record.timestamp.date() <= today:
            words_in_week += 1
            if words_in_week >= count:
                return True
    return False
