# LexiQ - 一款简洁的背单词软件

LexiQ 是一款用于背单词的在线软件，提供了简洁易用的界面和多种功能，帮助用户有效地学习和记忆单词。

## 功能特点

- 上传 CSV 文件：用户可以上传包含单词和释义的 CSV 文件，方便批量添加单词。
- 删除单词组：管理员可以删除不需要的单词组。
- 选择单词分组：用户可以选择要学习的单词分组，进行单词学习。
- 游戏模式：用户可以通过游戏模式进行单词学习，猜测单词并获得反馈。过程与wordle类似

## 技术栈

- Django：后端框架，处理网站逻辑和数据存储。
- HTML/CSS/JavaScript：前端开发，构建用户界面和实现交互功能。
- Bootstrap：前端 UI 框架，提供美观的界面组件。
- edge-tts：Python 库，用于生成单词的语音文件。
- SQLite：轻量级数据库，存储用户和单词数据。

## 使用说明

1. 克隆或下载项目到本地环境。
2. 启用虚拟环境
3. 安装 Python 依赖：`pip install -r requirements.txt`。
4. 迁移数据库：`python manage.py migrate`。
5. 生成静态文件`python manage.py collectstatic `
6. 运行开发服务器：`python manage.py runserver`。
7. 访问 `http://localhost:8000` 查看网站，并开始使用。
8. [这里](https://github.com/busiyiworld/maimemo-export/tree/main/libraries/csv)可以找到大量csv词库


## 许可证

本软件基于 GPLv3 许可证进行发布。详细信息请参阅 [LICENSE](LICENSE) 文件。

