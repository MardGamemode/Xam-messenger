import asyncio

import flet as fl

from Xam_Backend import Backend
from Xam_Style import BACKGROUND, GREEN, TEXT, MUTED
from Xam_Helpers import UIHelpersMixin
from Xam_Auth import AuthMixin
from Xam_ChatList import ChatListMixin
from Xam_Messages import MessagesMixin


class App(UIHelpersMixin, AuthMixin, ChatListMixin, MessagesMixin):
    def __init__(self, page: fl.Page, backend=None):
        self.page = page
        self.backend = Backend()
        self.username = ''
        self.current_chat = None
        self.chat_names = []
        self.current_raw_messages = []
        self.edit_target_index = None
        self.drafts = {}
        self.connected = True
        self.closed = False
        self.eula = self.backend.get_eula()[0]
        self.un = self.backend.get_eula()[1]
        self.eula_textbutt = fl.TextButton('Открыть политику конфиденциальности и примечания для пользователя',
                                           on_click=self.eula_def,
                                           style=fl.ButtonStyle(color=fl.Colors.BLUE, text_style=fl.TextStyle(size=8)))

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
            color_scheme_seed='#245B4D', font_family='Segoe UI',
            color_scheme=fl.ColorScheme(
                primary='#245B4D', on_primary='#FFFFFF',
                surface='#F5F4F0', surface_container_low='#FFFFFF',
                on_surface='#243431', on_surface_variant='#74817C',
                outline_variant='#E4E7E1', secondary_container='#E7EEDF',
                error='#B44336',
            ),
        )
        self.page.dark_theme = fl.Theme(
            color_scheme_seed='#245B4D', font_family='Segoe UI',
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

    def build_messenger(self):
        self.build_sidebar()
        self.build_conversation()
        self.chat_panel = fl.Container(
            expand=True, content=fl.Column([self.welcome, self.conversation], spacing=0, expand=True),
        )
        self.messenger = fl.Row([self.sidebar, self.chat_panel], spacing=0, expand=True)

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

    async def show_messenger(self):
        self.profile_name.value = self.username
        self.root.content = self.messenger
        self.resize()
        await self.refresh_chats()

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
