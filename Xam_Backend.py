import os
import sys
import io
import yadisk
from cryptography.fernet import Fernet
from dotenv import load_dotenv


class Backend:
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    load_dotenv(os.path.join(base_path, 'secretdata.env'))

    def __init__(self):
        self.token = os.getenv('YATOKEN')
        self.key1 = os.getenv('ENCRYPTION_KEY')
        self.key = self.key1.encode('utf-8')
        self.y = yadisk.YaDisk(token=self.token)
        self.flag = True
        self.frase = Fernet(self.key).encrypt('эта фраза должна уберегать файлы от исправления'.encode('utf-8'))
        self.get_eula()

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

    def get_eula(self):
        buffer = io.BytesIO()
        self.y.download('/eula.txt', buffer)
        buffer.seek(0)
        eula1 = buffer.read().decode("utf-8")
        eula = eula1.split('@')[0]
        un = eula1.split('@')[1]
        return eula, un

    def get_chats(self):
        chats = []
        for item in self.y.listdir('/chats'):
            if self.a.split('@')[0] == item.name.split('@')[0]:
                chats.append(item.name.split('@')[1])
            if self.a.split('@')[0] == item.name.split('@')[1]:
                chats.append(item.name.split('@')[0])
        return chats

    def get_users(self):
        users = []
        for item in self.y.listdir('/users'):
            users.append(item.name.split('@')[0])
        return users

    def get_accounts(self):
        users = []
        for item in self.y.listdir('/users'):
            users.append(item.name)
        return users

    def prepare_message(self, message, secuser):
        username = self.a.split('@')[0]
        message = message.replace('@', '{sobachka}')
        message = message.replace('|', '{vertpalka}')
        new_message = '|' + message + '@' + username

        path1 = f'/chats/{username}@{secuser}'
        path2 = f'/chats/{secuser}@{username}'
        if self.y.exists(path1):
            chat_path = path1
        elif self.y.exists(path2):
            chat_path = path2
        else:
            print(path1)
            print(path2)
            return None

        self.y.download(f'{chat_path}/chat.txt', 'chat.txt')
        with open('chat.txt', 'rb') as f:
            encrypted_chat = f.read()

        if len(encrypted_chat) == 0:
            old_text = ''
        else:
            old_text = Fernet(self.key).decrypt(encrypted_chat).decode('utf-8')

        all_text = old_text + new_message
        encrypted = Fernet(self.key).encrypt(all_text.encode('utf-8'))
        with open('chat.txt', 'wb') as f:
            f.write(encrypted)
        return chat_path

    def upload_message(self, chat_path):
        self.y.upload('chat.txt', f'{chat_path}/chat.txt', overwrite=True)

    def edit_message(self, secuser, index, new_text):
        """Изменяет уже отправленное сообщение по его индексу в списке,
        возвращаемом read_messages. Редактировать можно только свои сообщения."""
        username = self.a.split('@')[0]

        path1 = f'/chats/{username}@{secuser}'
        path2 = f'/chats/{secuser}@{username}'
        if self.y.exists(path1):
            chat_path = path1
        elif self.y.exists(path2):
            chat_path = path2
        else:
            return False

        self.y.download(f'{chat_path}/chat.txt', 'chat.txt')
        with open('chat.txt', 'rb') as f:
            encrypted_chat = f.read()

        if len(encrypted_chat) == 0:
            return False

        full_text = Fernet(self.key).decrypt(encrypted_chat).decode('utf-8')
        parts = full_text.split('|')
        # parts[0] — служебная фраза, не сообщение; настоящие сообщения начинаются с parts[1],
        # что соответствует индексам 0.. в списке, который возвращает read_messages.
        real_index = index + 1
        if real_index <= 0 or real_index >= len(parts):
            return False

        entry = parts[real_index]
        if '@' not in entry:
            return False
        _, author = entry.rsplit('@', 1)
        if author != username:
            return False

        new_text = new_text.replace('@', '{sobachka}').replace('|', '{vertpalka}')
        parts[real_index] = f'{new_text} (ред.)@{author}'

        new_full_text = '|'.join(parts)
        encrypted = Fernet(self.key).encrypt(new_full_text.encode('utf-8'))
        with open('chat.txt', 'wb') as f:
            f.write(encrypted)
        self.y.upload('chat.txt', f'{chat_path}/chat.txt', overwrite=True)
        return True

    def start_chat(self):
        with open('messages.txt', 'w') as f:
            f.write('0')
        with open('chat.txt', 'wb') as f:
            f.write(self.frase)

    def read_messages(self, secuser):
        print(f'/chats/{secuser}@{self.a.split('@')[0]}/chat.txt', f'/chats/{self.a.split('@')[0]}@{secuser}/chat.txt')
        try:
            self.y.download(f'/chats/{self.a.split('@')[0]}@{secuser}/chat.txt', 'chat.txt')
        except yadisk.exceptions.PathNotFoundError:
            self.y.download(f'/chats/{secuser}@{self.a.split('@')[0]}/chat.txt', 'chat.txt')
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
        return infile, messages, old_mess

    def finish_chat(self):
        with open('chat.txt', 'wb') as f:
            f.write(self.frase)
        with open('messages.txt', 'w') as f:
            f.write('0')

    def chat_exists(self, abc):
        a = self.a.split('@')[0]
        return self.y.exists(f'/chats/{a}@{abc}') or self.y.exists(f'/chats/{abc}@{a}')

    def create_chat(self, abc):
        a = self.a.split('@')[0]
        with open('chat.txt', 'wb') as f:
            f.write(self.frase)
        self.y.mkdir(f'/chats/{a}@{abc}')
        self.y.upload('chat.txt', f'/chats/{a}@{abc}/chat.txt')

    def logout(self):
        with open('user_inf.txt', 'w') as f:
            f.write('')

    def register(self, login, password):
        with open('user_inf.txt', 'w') as f:
            f.write(login + '@' + password)
        self.y.mkdir(f'/users/{login}@{password}')

    def login(self, login, password):
        users1 = self.get_accounts()
        for i in users1:
            if f'{login}@{password}' == i:
                with open('user_inf.txt', 'w') as f:
                    f.write(i)
                return True
        return False

    def check_account(self):
        if self.a == '':
            return False

        users1 = self.get_accounts()
        p = 0
        for i in users1:
            if self.a != i:
                p += 1
        print(self.a)
        print(p)
        print(users1)
        if p == len(users1):
            self.logout()
            return False
        return True
