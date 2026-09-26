import asyncio

import flet as fl

from Xam_Style import SIDEBAR, SIDEBAR_HOVER, ACCENT, MUTED


class ChatListMixin:
    def build_sidebar(self):
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
