from django.shortcuts import render, redirect
from .models import Word, WordGroup
from django.http import JsonResponse,HttpResponse
from django.contrib import messages
import csv,random,edge_tts,os
from io import TextIOWrapper
from .forms import UploadCSVForm,WordGroupForm
from django.contrib.admin.views.decorators import staff_member_required







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
        words_by_group[group] = Word.objects.filter(group=group)  # 获取每个分组下的单词列表，ord.objects.filter(group=group) 使用Word模型的objects管理器的filter方法过滤group字段等于当前循环的group的值
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
                word = random.choice(words)
                context = {
                    'word': word,
                    'success_message': 'Congratulations! You guessed the word correctly.'
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
                'error_message': 'Your guess is incorrect. Please try again.',
                'last_guess': last_guess
            }
            return render(request, 'wordapp/game.html', context)
    else:
        words = Word.objects.filter(group_id=group_id)
        if words.exists():
            word = random.choice(words)
            context = {
                'word': word,
            }
            return render(request, 'wordapp/game.html', context)
        else:
            return redirect('start_game')

def get_feedback(actual_word, guessed_word):
    feedback = []
    for i in range(len(actual_word)):
        if guessed_word[i] == actual_word[i]:
            feedback.append('green')  # 绿色表示字母和位置都正确
        elif guessed_word[i] in actual_word:
            feedback.append('yellow')  # 黄色表示字母正确但位置不正确
        else:
            feedback.append('gray')  # 灰色表示字母不在答案中
    return feedback


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

async def tts(request, word):#异步
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