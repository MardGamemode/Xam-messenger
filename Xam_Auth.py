import asyncio

import flet as fl

from Xam_Style import BACKGROUND, SURFACE, GREEN, TEXT, MUTED, BORDER, ERROR, ACCENT, SIDEBAR


class AuthMixin:
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
                self.eula_textbutt,
            ], horizontal_alignment=fl.CrossAxisAlignment.CENTER,
                alignment=fl.MainAxisAlignment.CENTER, scroll=fl.ScrollMode.AUTO),
        )

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

    def show_login(self):
        self.root.content = self.login_screen
        self.password_field.value = ''
        self.login_error.visible = False
        self.page.update()

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

    def show_account(self, e=None):
        self.page.show_dialog(fl.AlertDialog(
            title=fl.Text('Мой аккаунт'),
            content=fl.Column([
                self.make_avatar(self.username), fl.Text(self.username, size=20, color=TEXT),
                fl.Text('Вы вошли в XAM. Ваши чаты доступны в списке слева.', color=MUTED),
                self.eula_textbutt
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
                self.current_raw_messages = []
                self.messages.controls = []
                self.message_field.value = ''
                self.search_field.value = ''
                self.conversation.visible = False
                self.welcome.visible = True
            self.close_dialog()
            self.show_login()
        except Exception:
            self.notify('Не удалось выйти. Попробуйте ещё раз.')
