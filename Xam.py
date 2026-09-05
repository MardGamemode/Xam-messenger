import flet as fl
import yadisk
import time
import threading
from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv

class App:

    load_dotenv(dotenv_path='secretdata.env')

    def __init__(self, page: fl.Page):

        self.token = os.getenv('YATOKEN')
        self.key1 = os.getenv('ENCRYPTION_KEY')
        self.key = self.key1.encode('utf-8')

        self.page = page
        self.y = yadisk.YaDisk(token=self.token)

        self.page.title = 'Xam messenger'
        self.page.padding = 40
        self.page.theme_mode = fl.ThemeMode.DARK

        self.stop_event = threading.Event()

        self.flag = True

        self.errorfile = fl.AlertDialog(content=fl.Container(fl.Text('Целосность файлов повреждена или они отсутствуют!')))
        self.page.add(self.errorfile)

        self.frase = Fernet(self.key).encrypt('эта фраза должна уберегать файлы от исправления'.encode('utf-8'))

        try:
            with open('user_inf.txt', 'r') as f:
                self.a = f.read()
        except FileNotFoundError:
            self.a = ''
            self.flag = False
        try:
            with open('messages.txt', 'r') as f:
                xz = f.read()
        except FileNotFoundError:
            self.flag = False
        try:
            with open('chat.txt', 'r') as f:
                xzx = f.read()
        except FileNotFoundError:
            self.flag = False

        # ВСЕ ПЕРЕМЕННЫЕ

        self.paused = True

        self.new_chat = fl.Button(
                'Новый чат',
                on_click=self.newchat
            )

        self.acount = fl.Button(
                'Аккаунт',
                on_click=self.account
            )

        self.text = fl.Text(
                'Поля не должны быть пустыми!',
                visible=False
            )

        self.text1 = fl.Text(
                'Такой пользователь существует!',
                visible=False
            )

        self.text2 = fl.Text(
                'Неправильные логин или пароль!',
                visible=False
            )

        self.login = fl.Text('Логин: ')
        self.password = fl.Text('Пароль: ')

        self.entry = fl.TextField()
        self.entry2 = fl.TextField()
        self.entry_chat = fl.TextField()
        self.sendbutt = fl.Button('Отпр.', on_click=self.send_chat)
        self.sendtext = fl.Text('Подождите пару секунд', visible=False)
        self.chat_column = fl.Container(content = fl.Column([]))

        self.texttext = fl.Text('Такой чат уже существует!', visible=True)

        self.cont = fl.Container(
                content=fl.Column([
                    fl.Text('Выберете пользователя:')
                ])
            )

        self.cont_on_main = fl.Container(
                content=fl.Column([])
            )

        self.dialog = fl.AlertDialog(
                content=fl.Column([
                    fl.Text('Введите логин и пароль:'),
                    self.entry,
                    self.entry2,
                    fl.Button(
                        'Войти',
                        on_click=self.close_dialog2
                    ),
                    fl.Button(
                        'Зарегестрироваться',
                        on_click=self.close_dialog
                    ),
                    self.text,
                    self.text1,
                    self.text2
                ])
            )

        self.dialog1 = fl.AlertDialog(
                content=self.cont
            )

        self.dialog2 = fl.AlertDialog(
                content=fl.Column([
                    self.login,
                    self.password,
                    fl.Button(
                        'Выйти из аккаунта',
                        on_click=self.logout
                    ),
                ])
            )

        self.dialog_chat = fl.AlertDialog(
                content = fl.Column([
                    fl.Button('Выход', on_click=self.exitfromchat),
                    fl.Container(
                        content=fl.Column([
                    self.chat_column,
                    fl.Row([
                    self.entry_chat,
                    self.sendbutt,
                    self.sendtext
                    ])],
                    alignment=fl.MainAxisAlignment.SPACE_BETWEEN)
                    )

                ], scroll = fl.ScrollMode.AUTO)
            )

        self.state = {
                "thread": None,
                "stop_event": threading.Event(),
            }

        self.dialog3 = fl.AlertDialog(
            fl.Text('Приложение закроется через 5 секунд и вы выйдете из аккаунта')
        )
        self.dialog4 = fl.AlertDialog(
            fl.Text('Приложение закроется через 5 секунд и вы войдёте в аккаунт')
        )

        if self.flag:
            self.page.overlay.extend([
                self.dialog, self.dialog1, self.dialog2,
                self.dialog_chat, self.dialog3, self.dialog4
            ])
            self.page.add(self.new_chat, self.acount, self.cont_on_main)
        else:
            self.errorfile.open = True
            self.page.update()
            timer = threading.Timer(5.0, self.exit)
            timer.start()

        self.check_account()

        for item in self.y.listdir("/chats"):

                if self.a.split('@')[0] == item.name.split('@')[0]:
                    self.cont_on_main.content.controls.append(
                        fl.Button(item.name.split('@')[1], on_click=lambda _, name=item.name.split('@')[1]: self.page.run_thread(self.chat, name)))
                if self.a.split('@')[0] == item.name.split('@')[1]:
                    self.cont_on_main.content.controls.append(
                    fl.Button(item.name.split('@')[0], on_click=lambda _, name=item.name.split('@')[0]: self.page.run_thread(self.chat, name)))

    #ФУНКЦИЯ: ЗАКРЫВАЕТ ОКНО(подфункция)

    async def exit_pod(self):
        await self.page.window.close()

    # ФУНКЦИЯ: ЗАКРЫВАЕТ ОКНО

    def exit(self):
        self.page.run_task(self.exit_pod)

        # ФУНКЦИЯ: ОТПРАВКА СООБЩЕНИЯ
    def send_chat(self):
            self.paused = False

            self.page.run_thread(self.chat2)

            message = self.entry_chat.value

            if message == '':
                self.paused = True
                return

            username = self.a.split('@')[0]

            message = message.replace('@', '{sobachka}')
            message = message.replace('|', '{vertpalka}')

            new_message = '|' + message + '@' + username


            try:
                path1 = f'/chats/{username}@{self.secuser}'
                path2 = f'/chats/{self.secuser}@{username}'

                if self.y.exists(path1):
                    chat_path = path1
                elif self.y.exists(path2):
                    chat_path = path2
                else:
                    print(path1)
                    print(path2)

                    self.paused = True
                    return

                self.y.download(
                    f'{chat_path}/chat.txt',
                    'chat.txt'
                )

                with open('chat.txt', 'rb') as f:
                    encrypted_chat = f.read()

                if len(encrypted_chat) == 0:
                    old_text = ''
                else:
                    old_text = Fernet(self.key).decrypt(
                        encrypted_chat
                    ).decode('utf-8')

                all_text = old_text + new_message

                encrypted = Fernet(self.key).encrypt(
                    all_text.encode('utf-8')
                )

                with open('chat.txt', 'wb') as f:
                    f.write(encrypted)

                self.entry_chat.value = ''

                self.y.upload(
                    'chat.txt',
                    f'{chat_path}/chat.txt',
                    overwrite=True
                )

            except Exception as e:
                print('ОШИБКА ОТПРАВКИ:', e)

            finally:
                self.paused = True

    def chat2(self):
        self.sendbutt.visible = False
        self.sendtext.visible = True
        self.page.run_thread(self.dialog_chat.update)
        timer = threading.Timer(3.0, self.chat3)
        timer.start()

    def chat3(self):
        self.sendbutt.visible = True
        self.sendtext.visible = False
        self.page.run_thread(self.dialog_chat.update)

            # ФУНКЦИЯ: ЗАКРЫВАЕТ ДИАЛОГ С ЧАТОМ

    def exitfromchat(self):
                self.dialog_chat.open = False
                self.page.update()

            # ФУНКЦИЯ: ОТКРЫВАЕТ ДИАЛОГ С ВЫБОРОМ ПОЛЬЗОВАТЕЛЯ

    def newchat(self):
                a = self.a.split('@')[0]

                self.cont.content.controls = [fl.Text('Выберете пользователя:')]
                users = []

                for item in self.y.listdir("/users"):
                    users.append(item.name.split('@')[0])

                for papka in users:
                    if papka != a:
                        folder_name = papka

                        self.cont.content.controls.append(
                            fl.Button(
                                f'{folder_name}',
                                on_click=lambda _, name=folder_name:
                                self.but_newchat(name)
                            )
                        )

                self.dialog1.open = True
                self.page.update()

            # ФУНКЦИЯ: ВЫЗЫВАЕТ ОКНО С ЧАТОМ
    def chat(self, abc):
                self.dialog_chat.open = True
                self.page.update()
                self.secuser = abc

                with open('messages.txt', 'w') as f:
                    f.write('0')
                with open('chat.txt', 'wb') as f:
                    f.write(self.frase)
                self.chat_column.content = fl.Column([])
                self.chat_column.update()

                while self.dialog_chat.open == True:
                    if self.paused:
                        print(f'/chats/{self.secuser}@{self.a.split('@')[0]}/chat.txt', f'/chats/{self.a.split('@')[0]}@{self.secuser}/chat.txt')
                        try:
                            self.y.download(f'/chats/{self.a.split('@')[0]}@{self.secuser}/chat.txt', 'chat.txt')
                        except yadisk.exceptions.PathNotFoundError:
                            self.y.download(f'/chats/{self.secuser}@{self.a.split('@')[0]}/chat.txt', 'chat.txt')
                        with open('chat.txt', 'r') as f:
                            self.chattext = f.read()
                            infile = Fernet(self.key).decrypt(self.chattext).decode('utf-8').split('|')
                            infile.pop(0)
                        with open('messages.txt', 'r') as f:
                            old_mess = int(f.read())
                        messages = len(infile)
                        print(infile, messages, old_mess)
                        with open('messages.txt', 'w') as f:
                            f.write(str(messages))

                        if messages > old_mess:
                            new_controls = list(self.chat_column.content.controls)
                            for i in infile[old_mess:]:
                                new_controls.append(fl.Text(f'"{i.split('@')[0].replace('{sobachka}', '@').replace('{vertpalka}','|')}" от {i.split('@')[1]}'))
                            self.chat_column.content = fl.Column(new_controls)
                            self.chat_column.update()
                            self.page.run_thread(self.update_dialog)

                        print(self.chat_column.content.controls)
                        time.sleep(1)
                else:
                    self.chat_column.content = fl.Column([])
                    self.chat_column.update()
                    with open('chat.txt', 'wb') as f:
                        f.write(self.frase)
                    with open('messages.txt', 'w') as f:
                        f.write('0')
                    print(self.chat_column.content.controls)

            # ФУНКЦИЯ: ОТКРЫВАЕТ ОКНО С ИНФОРМАЦИЕЙ ОБ АККАУНТЕ

    def update_dialog(self):
        while self.dialog_chat.open == True:
            self.dialog_chat.update()

    def account(self, e=None):
                login_ = self.a.split("@")[0]
                password_ = self.a.split("@")[1]

                self.login.value = f'Логин: {login_}'
                self.password.value = f'Пароль: {password_}'

                self.dialog2.open = True
                self.page.update()


            # ФУНКЦИЯ: СОЗДАЕТ КНОПКИ ЧАТА

    def but_newchat(self, abc):
                a = self.a.split('@')[0]
                if self.texttext in self.cont.content.controls:
                    self.cont.content.controls.remove(self.texttext)


                if not (self.y.exists(f'/chats/{a}@{abc}') or self.y.exists(f'/chats/{abc}@{a}')):
                    self.dialog1.open = False
                    self.page.update()

                    with open('chat.txt', 'wb') as f:
                        f.write(self.frase)

                    self.y.mkdir(f'/chats/{a}@{abc}')
                    self.y.upload(
                        "chat.txt",
                        f"/chats/{a}@{abc}/chat.txt"
                    )

                    folder_name = abc

                    self.cont_on_main.content.controls.append(
                        fl.Button(folder_name, on_click=lambda _, name=folder_name: self.page.run_thread(self.chat, name))
                    )

                    self.page.update()

                else:
                    self.cont.content.controls.append(self.texttext)
                    self.page.update()

            # ФУНКЦИЯ: ВЫХОД ИЗ АККАУНТА

    def logout(self, e=None):
                with open('user_inf.txt', 'w') as f:
                    f.write('')

                self.dialog2.open = False
                self.dialog3.open = True
                self.page.update()
                timer = threading.Timer(5.0, self.exit)
                timer.start()

            # ФУНКЦИЯ: РЕГИСТРАЦИЯ ПОЛЬЗОВАТЕЛЯ

    def close_dialog(self, e=None):
                self.text.visible = False
                self.text1.visible = False

                users1 = []

                for item in self.y.listdir("/users"):
                    users1.append(item.name.split('@')[0])

                if self.entry.value == '' or self.entry2.value == '':
                    self.text.visible = True

                elif self.entry.value in users1:
                    self.text1.visible = True

                else:
                    self.dialog.open = False
                    self.page.update()

                    with open('user_inf.txt', 'w') as f:
                        f.write(
                            self.entry.value +
                            '@' +
                            self.entry2.value
                        )

                    self.y.mkdir(
                        f"/users/{self.entry.value}@{self.entry2.value}"
                    )
                self.dialog4.open = True
                self.page.update()
                timer = threading.Timer(5.0, self.exit)
                timer.start()

            # ФУНКЦИЯ: ВХОД ПОЛЬЗОВАТЕЛЯ

    def close_dialog2(self, e=None):
                self.text.visible = False
                self.text1.visible = False
                self.text2.visible = False

                users1 = []
                flag = True

                for item in self.y.listdir("/users"):
                    users1.append(item.name)

                for i in users1:
                    if f'{self.entry.value}@{self.entry2.value}' == i:

                        with open('user_inf.txt', 'w') as f:
                            f.write(i)

                        self.dialog.open = False
                        break

                else:
                    self.text2.visible = True
                    flag = False

                self.page.update()
                if flag:
                    self.dialog4.open = True
                    self.page.update()
                    timer = threading.Timer(5.0, self.exit)
                    timer.start()

            # ФУНКЦИЯ: ПРОВЕРКА АККАУНТА И ЕГО НАЛИЧИЕ

    def check_account(self):
                if self.a == '':
                    self.dialog.open = True
                    self.page.update()

                else:
                    users1 = []

                    for item in self.y.listdir("/users"):
                        users1.append(item.name)

                    p = 0

                    for i in users1:
                        if self.a != i:
                            p += 1

                    print(self.a)
                    print(p)
                    print(users1)

                    if p == len(users1):
                        with open('user_inf.txt', 'w') as f:
                            f.write('')

                        self.dialog.open = True
                        self.page.update()

fl.app(target=App)