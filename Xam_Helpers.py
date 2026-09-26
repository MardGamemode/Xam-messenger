import flet as fl

from Xam_Style import ACCENT, GREEN, SIDEBAR, SIDEBAR_HOVER


class UIHelpersMixin:
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

    def notify(self, message):
        self.page.show_dialog(fl.SnackBar(
            content=fl.Text(message, color=fl.Colors.WHITE), bgcolor=SIDEBAR,
        ))

    def close_dialog(self, e=None):
        self.page.pop_dialog()

    def resize(self, e=None):
        # На узком экране показываем только список или только переписку.
        narrow = (self.page.width or 1160) < 760
        self.sidebar.visible = not narrow or self.current_chat is None
        self.sidebar.width = None if narrow else 300
        self.sidebar.expand = narrow
        self.chat_panel.visible = not narrow or self.current_chat is not None
        self.page.update()
