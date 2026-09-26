import asyncio

import flet as fl

from Xam_Style import SURFACE, MESSAGE_BACKGROUND, TEXT, MUTED, BORDER, GREEN, ERROR


class MessagesMixin:
    def build_conversation(self):
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
        self.edit_field = fl.TextField(
            hint_text='Изменить сообщение…', multiline=True, min_lines=1, max_lines=4,
            border_radius=14, border_color=BORDER, focused_border_color=GREEN,
            bgcolor=SURFACE, text_size=15, content_padding=16, max_length=700,
            autofocus=True, on_submit=self.confirm_edit,
        )
        self.edit_error = fl.Text(color=ERROR, size=12, visible=False)
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
            self.current_raw_messages = []
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

    def make_message(self, index, message):
        text, author = message.rsplit('@', 1)
        text = text.replace('{sobachka}', '@').replace('{vertpalka}', '|')
        outgoing = author == self.username
        header = [
            fl.Text('Вы' if outgoing else author, size=11,
                    color='#D4E6D6' if outgoing else MUTED, weight=fl.FontWeight.W_600),
        ]
        if outgoing:
            header.append(fl.Container(expand=True))
            header.append(fl.IconButton(
                fl.Icons.EDIT_OUTLINED, icon_size=14, icon_color='#D4E6D6',
                width=22, height=22, data=index, tooltip='Изменить сообщение',
                on_click=self.start_edit,
            ))
        bubble = fl.Container(
            padding=16, border_radius=18, bgcolor=MESSAGE_BACKGROUND if outgoing else SURFACE,
            content=fl.Column([
                fl.Row(header, spacing=0),
                fl.Text(text, size=15, color=fl.Colors.WHITE if outgoing else TEXT, selectable=True,
                        weight=fl.FontWeight.W_400),
            ], spacing=6, tight=True),
        )
        bubble.expand = 8
        space = fl.Container(expand=2)
        return fl.Row([space, bubble] if outgoing else [bubble, space])

    def start_edit(self, e):
        index = e.control.data
        if index is None or index >= len(self.current_raw_messages):
            return
        raw = self.current_raw_messages[index]
        text, author = raw.rsplit('@', 1)
        if author != self.username:
            return
        text = text.replace('{sobachka}', '@').replace('{vertpalka}', '|')
        if text.endswith(' (ред.)'):
            text = text[:-len(' (ред.)')]
        self.edit_target_index = index
        self.edit_field.value = text
        self.edit_error.visible = False
        self.page.show_dialog(fl.AlertDialog(
            title=fl.Text('Изменить сообщение'),
            content=fl.Container(
                width=360,
                content=fl.Column([self.edit_field, self.edit_error], spacing=8, tight=True),
            ),
            actions=[
                fl.TextButton('Отмена', on_click=self.close_dialog),
                fl.TextButton('Сохранить', on_click=self.confirm_edit),
            ],
        ))
        self.page.update()

    async def confirm_edit(self, e=None):
        if self.edit_target_index is None or not self.current_chat:
            self.close_dialog()
            return
        new_text = self.edit_field.value.strip()
        if not new_text:
            self.edit_error.value = 'Сообщение не может быть пустым.'
            self.edit_error.visible = True
            self.page.update()
            return
        index = self.edit_target_index
        recipient = self.current_chat
        self.close_dialog()
        try:
            async with self.backend_lock:
                ok = await asyncio.to_thread(self.backend.edit_message, recipient, index, new_text)
            if not ok:
                self.notify('Не удалось изменить сообщение.')
            self.edit_target_index = None
            await self.load_messages()
        except Exception:
            self.notify('Не удалось изменить сообщение. Попробуйте ещё раз.')

    async def load_messages(self):
        async with self.backend_lock:
            if not self.current_chat:
                return
            try:
                messages, count, old_count = await asyncio.to_thread(
                    self.backend.read_messages, self.current_chat,
                )
                if messages != self.current_raw_messages:
                    self.current_raw_messages = messages
                    self.messages.controls = [
                        self.make_message(i, message) for i, message in enumerate(messages)
                    ]
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
