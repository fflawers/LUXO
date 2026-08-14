import flet as ft

class EmojiIconButton(ft.Container):
    def __init__(self, icon_emoji, active_emoji=None, icon_color=None, on_click=None, tooltip=None, **kwargs):
        self.icon_emoji = icon_emoji
        self.active_emoji = active_emoji or icon_emoji
        self.txt = ft.Text(icon_emoji, color=icon_color, size=18, text_align="center")
        self.on_click_callback = on_click
        
        super().__init__(
            content=self.txt,
            alignment=ft.alignment.Alignment(0, 0),
            on_click=self.handle_click,
            tooltip=tooltip,
            **kwargs
        )
        self._icon_color = icon_color
        self._icon = ""

    def handle_click(self, e):
        if self.on_click_callback:
            self.on_click_callback(e)

    @property
    def icon(self):
        return self._icon

    @icon.setter
    def icon(self, val):
        self._icon = val
        if val and ("stop" in str(val).lower() or "mic" not in str(val).lower()):
            self.txt.value = self.active_emoji
        else:
            self.txt.value = self.icon_emoji

    @property
    def icon_color(self):
        return self._icon_color

    @icon_color.setter
    def icon_color(self, val):
        self._icon_color = val
        self.txt.color = val


class EmojiDropdown(ft.Container):
    def __init__(self, label, options=None, value=None, on_change=None, width=None, height=45, border_color="#9D50BB", **kwargs):
        self.options_list = options or []
        self.selected_value = value
        self.on_change_callback = on_change
        
        self.label_text = ft.Text(label, color="#aaaaaa", size=9)
        self.val_text = ft.Text("", color="white", size=12, weight="bold")
        self.arrow_text = ft.Text("▼", color="#00FFFF", size=10)
        
        self.update_display_text()
        
        self.btn = ft.PopupMenuButton(
            content=ft.Container(
                content=ft.Column([
                    self.label_text,
                    ft.Row([
                        self.val_text,
                        self.arrow_text
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)
                ], spacing=2, alignment=ft.MainAxisAlignment.CENTER),
                border=ft.Border.all(1, border_color),
                border_radius=8,
                padding=ft.padding.Padding(10, 4, 10, 4),
                width=width,
                height=height,
                bgcolor="#161622",
                ink=True
            ),
            items=[]
        )
        self.rebuild_menu_items()
        
        super().__init__(
            content=self.btn,
            width=width,
            height=height,
            **kwargs
        )

    def update_display_text(self):
        found_text = ""
        for opt in self.options_list:
            opt_key = getattr(opt, "key", None) or getattr(opt, "value", None)
            if opt_key is None:
                opt_key = str(opt)
            opt_text = getattr(opt, "text", None) or getattr(opt, "label", None) or opt_key
            if str(opt_key) == str(self.selected_value):
                found_text = opt_text
                break
        if not found_text:
            found_text = str(self.selected_value) if self.selected_value is not None else ""
        self.val_text.value = found_text

    def rebuild_menu_items(self):
        menu_items = []
        for opt in self.options_list:
            opt_key = getattr(opt, "key", None) or getattr(opt, "value", None)
            if opt_key is None:
                opt_key = str(opt)
            opt_text = getattr(opt, "text", None) or getattr(opt, "label", None) or opt_key
            
            def make_select_click(k, t):
                return lambda e: self.select_value(k, t)
                
            menu_items.append(
                ft.PopupMenuItem(content=ft.Text(opt_text, color="white"), on_click=make_select_click(opt_key, opt_text))
            )
        self.btn.items = menu_items

    def select_value(self, key, text):
        self.selected_value = key
        self.val_text.value = text
        self.val_text.update()
        if self.on_change_callback:
            class DummyEvent:
                def __init__(self, control):
                    self.control = control
            self.on_change_callback(DummyEvent(self))

    @property
    def value(self):
        return self.selected_value

    @value.setter
    def value(self, val):
        self.selected_value = val
        self.update_display_text()
        try: self.val_text.update()
        except Exception: pass
        
    @property
    def options(self):
        return self.options_list
        
    @options.setter
    def options(self, val):
        self.options_list = val or []
        self.rebuild_menu_items()
        self.update_display_text()
        try:
            self.val_text.update()
            self.btn.update()
        except Exception: pass
