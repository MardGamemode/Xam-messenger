import asyncio

import flet as fl

from Xam_Backend import Backend
from eula import eula, un


BACKGROUND = fl.Colors.SURFACE
SURFACE = fl.Colors.SURFACE_CONTAINER_LOW
GREEN = fl.Colors.PRIMARY
TEXT = fl.Colors.ON_SURFACE
MUTED = fl.Colors.ON_SURFACE_VARIANT
BORDER = fl.Colors.OUTLINE_VARIANT
ERROR = fl.Colors.ERROR
 
SIDEBAR = '#153638'
SIDEBAR_HOVER = '#25494B'
ACCENT = '#D4F59B'
MESSAGE_BACKGROUND = '#245B4D'

class App:
    def __init__(self, page: fl.Page, backend=None):
        self.un = un
        self.eula = eula
        self.page = page
        self.backend = backend
        self.username = ''
        self.current_chat = None
        self.chat_names = []
        self.drafts = {}
        self.connected = True
        self.closed = False

        # Чтение и отправка используют один chat.txt: выполняем их по очереди.
        self.backend_lock = asyncio.Lock()

        self.configure_page()
        self.build_login_screen()
        self.build_messenger()
        self.root = fl.Container(expand=True, bgcolor=BACKGROUND)
        self.page.add(self.root)
        self.show_loading()
        self.page.run_task(self.start)

    def configure_page(self):
        self.page.title = 'XAM - мессенджер'
        self.page.padding = 0
        self.page.spacing = 0
        self.page.bgcolor = BACKGROUND
        # SYSTEM следит за темой устройства, в том числе во время работы.
        # Элементы интерфейса остаются на месте: меняются только их цвета.
        self.page.theme_mode = fl.ThemeMode.SYSTEM
        self.page.theme = fl.Theme(
            color_scheme_seed=MESSAGE_BACKGROUND, font_family='Segoe UI',
            color_scheme=fl.ColorScheme(
                primary='#245B4D', on_primary='#FFFFFF',
                surface='#F5F4F0', surface_container_low='#FFFFFF',
                on_surface='#243431', on_surface_variant='#74817C',
                outline_variant='#E4E7E1', secondary_container='#E7EEDF',
                error='#B44336',
            ),
        )
        self.page.dark_theme = fl.Theme(
            color_scheme_seed=MESSAGE_BACKGROUND, font_family='Segoe UI',
            color_scheme=fl.ColorScheme(
                primary='#B7DDA3', on_primary='#173825',
                surface='#101A19', surface_container_low='#1B2926',
                on_surface='#E5EEE8', on_surface_variant='#ABBAB1',
                outline_variant='#3B4B43', secondary_container='#2B3E30',
                error='#FFB4A8',
            ),
        )
        self.page.window.width = 1160
        self.page.window.height = 780
        self.page.window.min_width = 360
        self.page.window.min_height = 560
        self.page.on_resize = self.resize
        self.page.on_disconnect = self.disconnect
        self.page.on_connect = self.reconnect
        self.page.on_close = self.close

    def make_avatar(self, name, dark=False):
        return fl.Container(
            content=fl.Text(name[:1].upper() or '?', size=18, weight=fl.FontWeight.W_600,
                            color=ACCENT if dark else GREEN),
            width=42, height=42, border_radius=15,
            bgcolor=SIDEBAR_HOVER if dark else fl.Colors.SECONDARY_CONTAINER,
            alignment=fl.Alignment.CENTER,
        )

    def make_button(self, text, handler, icon=None):
        return fl.Button(
            text, icon=icon, on_click=handler, height=46,
            bgcolor=ACCENT, color=SIDEBAR, elevation=0,
            style=fl.ButtonStyle(shape=fl.RoundedRectangleBorder(radius=12)),
        )

    def build_login_screen(self):
        self.login_field = fl.TextField(
            label='Логин', autofocus=True, prefix_icon=fl.Icons.PERSON_OUTLINE,
            border_radius=12, border_color=BORDER, focused_border_color=GREEN,
            on_submit=self.sign_in,
        )
        self.password_field = fl.TextField(
            label='Пароль', password=True, can_reveal_password=True,
            prefix_icon=fl.Icons.LOCK_OUTLINE, border_radius=12,
            border_color=BORDER, focused_border_color=GREEN, on_submit=self.sign_in,
        )
        self.login_error = fl.Text(color=ERROR, size=13, visible=False)
        self.login_button = self.make_button('Войти', self.sign_in, fl.Icons.ARROW_FORWARD)
        self.login_button.width = 360
        self.register_button = fl.TextButton('Создать аккаунт', on_click=self.register)
        self.auth_form = fl.Column([
            self.login_field, self.password_field, self.login_error,
            self.login_button,
            fl.Row([self.register_button], alignment=fl.MainAxisAlignment.CENTER),
        ], spacing=16, tight=True, horizontal_alignment=fl.CrossAxisAlignment.STRETCH)
        self.login_screen = fl.Container(
            expand=True, alignment=fl.Alignment.CENTER, padding=24,
            content=fl.Column([
                fl.Container(
                    width=432, padding=32, border_radius=24, bgcolor=SURFACE,
                    border=fl.Border.all(1, BORDER),
                    content=fl.Column([
                        fl.Container(
                            content=fl.Icon(fl.Icons.FORUM_OUTLINED, color=ACCENT, size=30),
                            width=64, height=64, bgcolor=SIDEBAR, border_radius=20,
                            alignment=fl.Alignment.CENTER,
                        ),
                        fl.Text('XAM', size=34, weight=fl.FontWeight.W_700, color=TEXT),
                        fl.Divider(height=24, color=BORDER),
                        fl.Text('Добро пожаловать', size=22, weight=fl.FontWeight.W_600, color=TEXT),
                        fl.Text('Войдите или создайте аккаунт, чтобы начать общение.', color=MUTED),
                        self.auth_form,
                    ], spacing=16, tight=True),
                ),
                fl.Text('Нажимая кнопку "Войти" или "Создать аккаунт", вы автоматически соглашаетесь с политикой конфиденциальности и подтверждаете, что ознакомлены с примечаниями для пользователя.', color=MUTED, size=8),
                fl.TextButton('Открыть политику конфиденциальности и примечания для пользователя', on_click=self.eula_def, style=fl.ButtonStyle(color=fl.Colors.BLUE, text_style=fl.TextStyle(size=8))),
            ], horizontal_alignment=fl.CrossAxisAlignment.CENTER,
                alignment=fl.MainAxisAlignment.CENTER, scroll=fl.ScrollMode.AUTO),
        )

    def build_messenger(self):
        self.search_field = fl.TextField(
            hint_text='Найти чат', prefix_icon=fl.Icon(fl.Icons.SEARCH, color='#ADC0B9'),
            on_change=self.filter_chats, text_size=14, color=fl.Colors.WHITE,
            hint_style=fl.TextStyle(color='#ADC0B9'), bgcolor=SIDEBAR_HOVER,
            border_color=SIDEBAR_HOVER, focused_border_color=ACCENT,
            border_radius=12, content_padding=14,
        )
        self.chat_list = fl.ListView(expand=True, spacing=6, padding=0)
        self.chat_count = fl.Text('0', size=12, color='#ADC0B9')
        self.profile_name = fl.Text(color=fl.Colors.WHITE, weight=fl.FontWeight.W_600,
                                    max_lines=1, overflow=fl.TextOverflow.ELLIPSIS)
        self.new_chat_button = self.make_button('Новый чат', self.show_users, fl.Icons.ADD)
        self.new_chat_button.width = 260
        self.sidebar = fl.Container(
            width=300, bgcolor=SIDEBAR, padding=22,
            content=fl.Column([
                fl.Row([
                    fl.Icon(fl.Icons.FORUM_OUTLINED, color=ACCENT, size=28),
                    fl.Text('XAM', color=fl.Colors.WHITE, size=28, weight=fl.FontWeight.W_700),
                ], spacing=12),
                fl.Container(height=12),
                self.new_chat_button,
                self.search_field,
                fl.Container(
                    padding=fl.Padding.only(top=12, bottom=4),
                    content=fl.Row([
                        fl.Text('ВАШИ ЧАТЫ', color='#ADC0B9', size=11,
                                weight=fl.FontWeight.W_600, expand=True),
                        self.chat_count,
                        fl.IconButton(fl.Icons.REFRESH, icon_color='#ADC0B9',
                                      icon_size=18, tooltip='Обновить чаты', on_click=self.refresh_chats),
                    ]),
                ),
                self.chat_list,
                fl.Divider(color=SIDEBAR_HOVER),
                fl.Row([
                    fl.Icon(fl.Icons.ACCOUNT_CIRCLE_OUTLINED, color=ACCENT, size=30),
                    fl.Column([self.profile_name, fl.Text('Мой аккаунт', color='#ADC0B9', size=11)],
                              spacing=3, expand=True),
                    fl.IconButton(fl.Icons.MORE_HORIZ, icon_color=fl.Colors.WHITE,
                                  tooltip='Аккаунт', on_click=self.show_account),
                ]),
            ], spacing=12, expand=True, horizontal_alignment=fl.CrossAxisAlignment.STRETCH),
        )

        self.welcome = fl.Container(
            expand=True, alignment=fl.Alignment.CENTER, padding=28,
            content=fl.Column([
                fl.Container(
                    content=fl.Icon(fl.Icons.CHAT_BUBBLE_OUTLINE, size=48, color=GREEN),
                    width=104, height=104, bgcolor=fl.Colors.SECONDARY_CONTAINER, border_radius=32,
                    alignment=fl.Alignment.CENTER,
                ), fl.Text('Выберите чат слева \n или напишите кому-нибудь первым',
                        size=25, color=fl.Colors.WHITE, text_align=fl.TextAlign.CENTER),
                self.make_button('Начать разговор', self.show_users, fl.Icons.ADD),
            ], spacing=22, alignment=fl.MainAxisAlignment.CENTER,
                horizontal_alignment=fl.CrossAxisAlignment.CENTER, tight=True),
        )
        self.chat_title = fl.Text(size=19, weight=fl.FontWeight.W_600, color=TEXT,
                                  max_lines=1, overflow=fl.TextOverflow.ELLIPSIS)
        self.chat_status = fl.Text('Загружаем сообщения…', size=12, color=MUTED)
        self.header_avatar = self.make_avatar('?')
        self.messages = fl.ListView(expand=True, spacing=14, padding=24, auto_scroll=True)
        self.empty_chat = fl.Container(
            content=fl.Text('Здесь пока тихо. Отправьте первое сообщение.',
                            color=MUTED, text_align=fl.TextAlign.CENTER),
            padding=20, alignment=fl.Alignment.CENTER, visible=False,
        )
        self.message_field = fl.TextField(
            hint_text='Напишите сообщение…', expand=True, multiline=True,
            min_lines=1, max_lines=4, shift_enter=True, on_submit=self.send_message,
            border_radius=14, border_color=BORDER, focused_border_color=GREEN,
            bgcolor=SURFACE, text_size=15, content_padding=16, max_length=700
        )
        self.send_button = fl.IconButton(
            fl.Icons.ARROW_UPWARD, tooltip='Отправить сообщение', on_click=self.send_message,
            bgcolor=GREEN, icon_color=fl.Colors.ON_PRIMARY, width=48, height=48,
        )
        self.composer = fl.Container(
            padding=fl.Padding.only(left=24, right=24, top=12, bottom=18),
            content=fl.Column([
                fl.Row([self.message_field, self.send_button], spacing=12,
                       vertical_alignment=fl.CrossAxisAlignment.END),
                fl.Text('Enter — отправить · Shift + Enter — новая строка', size=11, color=MUTED),
            ], spacing=8),
        )
        self.conversation = fl.Column([
            fl.Container(
                bgcolor=SURFACE, padding=18,
                border=fl.Border(bottom=fl.BorderSide(1, BORDER)),
                content=fl.Row([
                    fl.IconButton(fl.Icons.ARROW_BACK, tooltip='Назад к чатам', on_click=self.back_to_chats),
                    self.header_avatar,
                    fl.Column([self.chat_title, self.chat_status], spacing=4, expand=True),
                    fl.Icon(fl.Icons.CHAT_OUTLINED, color=MUTED, size=22),
                ], spacing=12),
            ),
            self.empty_chat, self.messages, self.composer,
        ], spacing=0, expand=True, visible=False)
        self.chat_panel = fl.Container(
            expand=True, content=fl.Column([self.welcome, self.conversation], spacing=0, expand=True),
        )
        self.messenger = fl.Row([self.sidebar, self.chat_panel], spacing=0, expand=True)

    def eula_def(self):
        self.dialog = fl.AlertDialog(title="Политика конфиденциальности и примечания для пользователя",
                        content = fl.Column([
                        fl.Text('Политика конфиденциальности', size=16),
                        fl.Text(self.eula, size=10),
                        fl.Text('Примечания для пользователя', size=16),
                        fl.Text(self.un, size=10),
                        fl.TextButton('Выход', on_click=self.eula_def_close)
                        ],scroll=fl.ScrollMode.AUTO
                        )
                        )
        self.page.show_dialog(self.dialog)
        self.page.update()

    def eula_def_close(self):
        self.dialog.open = False
        self.page.update()

    def show_loading(self):
        self.root.content = fl.Column([
            fl.ProgressRing(color=GREEN), fl.Text('Открываем XAM…', color=MUTED),
        ], alignment=fl.MainAxisAlignment.CENTER, horizontal_alignment=fl.CrossAxisAlignment.CENTER)
        self.page.update()

    async def start(self):
        try:
            if self.backend is None:
                self.backend = await asyncio.to_thread(Backend)
            if not self.backend.flag:
                self.show_start_error('Не найдены файлы user_inf.txt, messages.txt или chat.txt.')
                return
            account_exists = await asyncio.to_thread(self.backend.check_account)
            if account_exists:
                self.username = self.backend.a.split('@')[0]
                await self.show_messenger()
            else:
                self.show_login()
        except Exception:
            self.show_start_error('Не удалось открыть приложение. Проверьте настройки и подключение к интернету.')
            return
        self.page.run_task(self.poll_messages)

    def show_start_error(self, message):
        self.root.content = fl.Container(
            alignment=fl.Alignment.CENTER, padding=32,
            content=fl.Column([
                fl.Icon(fl.Icons.CLOUD_OFF_OUTLINED, size=48, color=GREEN),
                fl.Text('Не удалось подключиться', size=24, color=TEXT),
                fl.Text(message, color=MUTED, text_align=fl.TextAlign.CENTER),
                self.make_button('Попробовать снова', self.retry_start, fl.Icons.REFRESH),
            ], alignment=fl.MainAxisAlignment.CENTER,
                horizontal_alignment=fl.CrossAxisAlignment.CENTER, spacing=20),
        )
        self.page.update()

    async def retry_start(self, e):
        e.control.disabled = True
        self.show_loading()
        self.backend = None
        await self.start()

    def show_login(self):
        self.root.content = self.login_screen
        self.password_field.value = ''
        self.login_error.visible = False
        self.page.update()

    async def show_messenger(self):
        self.profile_name.value = self.username
        self.root.content = self.messenger
        self.resize()
        await self.refresh_chats()

    def resize(self, e=None):
        # На узком экране показываем только список или только переписку.
        narrow = (self.page.width or 1160) < 760
        self.sidebar.visible = not narrow or self.current_chat is None
        self.sidebar.width = None if narrow else 300
        self.sidebar.expand = narrow
        self.chat_panel.visible = not narrow or self.current_chat is not None
        self.page.update()

    def notify(self, message):
        self.page.show_dialog(fl.SnackBar(
            content=fl.Text(message, color=fl.Colors.WHITE), bgcolor=SIDEBAR,
        ))

    async def sign_in(self, e=None):
        await self.submit_account(register=False)

    async def register(self, e=None):
        await self.submit_account(register=True)

    async def submit_account(self, register):
        if self.auth_form.disabled:
            return
        login = self.login_field.value.strip()
        password = self.password_field.value
        self.login_error.visible = False
        if not login or not password.strip():
            self.login_error.value = 'Введите логин и пароль.'
        elif '@' in login or '@' in password or '/' in login or '\\' in login:
            self.login_error.value = 'В логине нельзя использовать @, / и \\. В пароле — @.'
        else:
            self.auth_form.disabled = True
            self.login_button.content = 'Подождите…'
            self.page.update()
            try:
                async with self.backend_lock:
                    if register:
                        users = await asyncio.to_thread(self.backend.get_users)
                        if login in users:
                            self.login_error.value = 'Этот логин уже занят. Выберите другой.'
                            self.login_error.visible = True
                            return
                        await asyncio.to_thread(self.backend.register, login, password)
                    else:
                        success = await asyncio.to_thread(self.backend.login, login, password)
                        if not success:
                            self.login_error.value = 'Неверный логин или пароль.'
                            self.login_error.visible = True
                            return
                    # Backend хранит текущую учётную запись в атрибуте a.
                    self.backend.a = login + '@' + password
                    self.username = login
                self.password_field.value = ''
                await self.show_messenger()
                return
            except Exception:
                self.login_error.value = 'Не удалось войти. Проверьте интернет и попробуйте снова.'
            finally:
                self.auth_form.disabled = False
                self.login_button.content = 'Войти'
                self.page.update()
        self.login_error.visible = True
        self.page.update()

    async def refresh_chats(self, e=None):
        try:
            async with self.backend_lock:
                names = await asyncio.to_thread(self.backend.get_chats)
                self.chat_names = sorted(set(names), key=str.casefold)
            self.filter_chats()
        except Exception:
            self.notify('Не удалось загрузить чаты. Нажмите кнопку обновления, чтобы повторить.')

    def filter_chats(self, e=None):
        query = self.search_field.value.strip().casefold()
        self.chat_list.controls = []
        self.chat_count.value = str(len(self.chat_names))
        for name in self.chat_names:
            if query not in name.casefold():
                continue
            selected = name == self.current_chat
            self.chat_list.controls.append(fl.Container(
                data=name, on_click=self.open_chat_event, ink=True,
                padding=12, border_radius=14,
                bgcolor=SIDEBAR_HOVER if selected else SIDEBAR,
                content=fl.Row([
                    self.make_avatar(name, dark=True),
                    fl.Column([
                        fl.Text(name, color=fl.Colors.WHITE, weight=fl.FontWeight.W_600,
                                max_lines=1, overflow=fl.TextOverflow.ELLIPSIS),
                        fl.Text('Открыт' if selected else 'Личная переписка', size=11, color='#ADC0B9'),
                    ], spacing=5, expand=True),
                    fl.Icon(fl.Icons.CHEVRON_RIGHT, size=18, color=ACCENT if selected else '#ADC0B9'),
                ], spacing=10),
            ))
        if not self.chat_list.controls:
            text = 'Ничего не найдено' if query else 'Пока нет чатов.\nНачните первый разговор.'
            self.chat_list.controls.append(fl.Container(
                content=fl.Text(text, color='#ADC0B9', size=13), padding=12,
            ))
        self.page.update()

    async def show_users(self, e=None):
        if self.new_chat_button.disabled:
            return
        self.new_chat_button.disabled = True
        self.page.update()
        try:
            async with self.backend_lock:
                users = await asyncio.to_thread(self.backend.get_users)
            choices = []
            for name in sorted(set(users), key=str.casefold):
                if name != self.username:
                    choices.append(fl.ListTile(
                        leading=self.make_avatar(name), title=fl.Text(name),
                        subtitle=fl.Text('Начать разговор'), data=name, on_click=self.choose_user,
                    ))
            if not choices:
                choices.append(fl.Text('Других пользователей пока нет.', color=MUTED))
            self.page.show_dialog(fl.AlertDialog(
                title=fl.Text('Новый разговор'),
                content=fl.Container(width=360, height=320, content=fl.ListView(choices, spacing=8)),
                actions=[fl.TextButton('Отмена', on_click=self.close_dialog)],
            ))
        except Exception:
            self.notify('Не удалось загрузить пользователей. Попробуйте ещё раз.')
        finally:
            self.new_chat_button.disabled = False
            self.page.update()

    def close_dialog(self, e=None):
        self.page.pop_dialog()

    async def choose_user(self, e):
        name = e.control.data
        self.close_dialog()
        try:
            async with self.backend_lock:
                exists = await asyncio.to_thread(self.backend.chat_exists, name)
                if not exists:
                    await asyncio.to_thread(self.backend.create_chat, name)
            await self.refresh_chats()
            await self.open_chat(name)
        except Exception:
            self.notify('Не удалось создать чат. Попробуйте ещё раз.')

    async def open_chat_event(self, e):
        await self.open_chat(e.control.data)

    async def open_chat(self, name):
        async with self.backend_lock:
            if name == self.current_chat:
                return
            try:
                await asyncio.to_thread(self.backend.start_chat)
            except Exception:
                self.notify('Не удалось открыть локальные файлы чата.')
                return
            if self.current_chat:
                self.drafts[self.current_chat] = self.message_field.value
            self.current_chat = name
            self.message_field.value = self.drafts.get(name, '')
            self.chat_title.value = name
            self.chat_status.value = 'Загружаем сообщения…'
            self.header_avatar.content.value = name[:1].upper()
            self.messages.controls = []
            self.empty_chat.visible = False
            self.welcome.visible = False
            self.conversation.visible = True
            self.filter_chats()
            self.resize()
        await self.load_messages()

    async def back_to_chats(self, e=None):
        async with self.backend_lock:
            if self.current_chat:
                self.drafts[self.current_chat] = self.message_field.value
            self.current_chat = None
            self.conversation.visible = False
            self.welcome.visible = True
            self.filter_chats()
            self.resize()

    def make_message(self, message):
        text, author = message.rsplit('@', 1)
        text = text.replace('{sobachka}', '@').replace('{vertpalka}', '|')
        outgoing = author == self.username
        bubble = fl.Container(
            padding=16, border_radius=18, bgcolor=MESSAGE_BACKGROUND if outgoing else SURFACE,
            content=fl.Column([
                fl.Text('Вы' if outgoing else author, size=11,
                        color='#D4E6D6' if outgoing else MUTED, weight=fl.FontWeight.W_600),
                fl.Text(text, size=15, color=fl.Colors.WHITE if outgoing else TEXT, selectable=True,
                        weight=fl.FontWeight.W_400),
            ], spacing=6, tight=True),
        )
        bubble.expand = 8
        space = fl.Container(expand=2)
        return fl.Row([space, bubble] if outgoing else [bubble, space])

    async def load_messages(self):
        async with self.backend_lock:
            if not self.current_chat:
                return
            try:
                messages, count, old_count = await asyncio.to_thread(
                    self.backend.read_messages, self.current_chat,
                )
                if count != len(self.messages.controls):
                    self.messages.controls = [self.make_message(message) for message in messages]
                self.empty_chat.visible = count == 0
                self.chat_status.value = 'Личная переписка'
                self.chat_status.color = MUTED
            except Exception:
                self.chat_status.value = 'Нет соединения. Пробуем снова…'
                self.chat_status.color = ERROR
            self.page.update()

    async def poll_messages(self):
        # Один цикл на приложение. Пауза не блокирует кнопки и другие события.
        while not self.closed:
            await asyncio.sleep(2)
            if self.connected and self.current_chat:
                await self.load_messages()

    async def send_message(self, e=None):
        message = self.message_field.value
        recipient = self.current_chat
        if not self.current_chat or not message.strip() or self.composer.disabled:
            return
        self.composer.disabled = True
        self.page.update()
        try:
            async with self.backend_lock:
                # Пока мы ждали, пользователь мог перейти в другой чат.
                if recipient != self.current_chat:
                    return
                chat_path = await asyncio.to_thread(
                    self.backend.prepare_message, message, recipient,
                )
                if chat_path is None:
                    self.notify('Чат не найден. Обновите список чатов.')
                    return
                await asyncio.to_thread(self.backend.upload_message, chat_path)
                # Очищаем ввод только после успешной отправки.
                self.message_field.value = ''
                self.drafts.pop(self.current_chat, None)
            await self.load_messages()
        except Exception:
            self.notify('Сообщение не отправлено. Текст сохранён — попробуйте ещё раз.')
        finally:
            self.composer.disabled = False
            self.page.update()

    def show_account(self, e=None):
        self.page.show_dialog(fl.AlertDialog(
            title=fl.Text('Мой аккаунт'),
            content=fl.Column([
                self.make_avatar(self.username), fl.Text(self.username, size=20, color=TEXT),
                fl.Text('Вы вошли в XAM. Ваши чаты доступны в списке слева.', color=MUTED),
            ], spacing=16, tight=True, width=300),
            actions=[fl.TextButton('Закрыть', on_click=self.close_dialog),
                     fl.TextButton('Выйти', on_click=self.logout)],
        ))

    async def logout(self, e=None):
        try:
            async with self.backend_lock:
                await asyncio.to_thread(self.backend.logout)
                self.backend.a = ''
                self.username = ''
                self.current_chat = None
                self.chat_names = []
                self.chat_list.controls = []
                self.chat_count.value = '0'
                self.drafts.clear()
                self.messages.controls = []
                self.message_field.value = ''
                self.search_field.value = ''
                self.conversation.visible = False
                self.welcome.visible = True
            self.close_dialog()
            self.show_login()
        except Exception:
            self.notify('Не удалось выйти. Попробуйте ещё раз.')

    def disconnect(self, e=None):
        self.connected = False

    def reconnect(self, e=None):
        self.connected = True
        self.resize()

    def close(self, e=None):
        self.closed = True


def main():
    fl.run(App)


if __name__ == '__main__':
    main()
