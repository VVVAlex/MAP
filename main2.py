# https://github.com/jacklinquan/usbserial4a

__version__ = "0.2"
__author__ = "Veresov Alex"
__email__ = "lexa1st@mail.ru"

import os
import sys
import time
from functools import partial

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp

# from kivy.properties import StringProperty
# from kivy.uix.boxlayout import BoxLayout
from kivy.utils import platform
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import (
    MDButton,
    MDButtonIcon,
    MDButtonText,
)
from kivymd.uix.label import MDLabel

# from kivymd.uix.list import OneLineIconListItem
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.screen import MDScreen
from PIL import Image, ImageChops

# from kivymd.uix.filemanager import MDFileManager
# from kivy.lang import Builder
# from kivy.uix.button import Button
# from kivy.clock import mainthread
# from kivymd.uix.tab import MDTabsBase
# from kivymd.uix.list import OneLineIconListItem
# from kivy.properties import BoundedNumericProperty

# Config.set("graphics", "resizable", 0)
# Config.set("kivy", "keyboard_mode", "systemanddock")  # экранная клав
# Config.set("kivy", "log_level", "error")                # убрать warning

# Window.size = (350, 520)
Window.size = (350, 520)


# Window.clearcolor = (1, 1, 1, 1)
# Builder.load_file('markap.kv')
# Builder.load_file('filechoser.kv')


if platform == "android":
    from android.permissions import Permission, request_permissions
    from usb4a import usb
    from usbserial4a import serial4a

    request_permissions(
        [Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE]
    )
    from android.storage import primary_external_storage_path

    primary_ext_storage = primary_external_storage_path()
else:
    from serial import Serial, SerialException
    from serial.tools import list_ports

    primary_ext_storage = os.path.split(os.path.abspath(__file__))[0]


# class Tab(MDFloatLayout, MDTabsBase):
# """Class implementing content for a tab."""


class FCooser(MDBoxLayout):
    """Filechooser + Image"""

    pathimg = os.path.join(primary_ext_storage, "mapimg")
    pth = None

    def selected(self, filename):
        self.pth = filename  # list
        try:
            im = Image.open(filename[0])
            if im.size[0] <= 32 or im.size[1] <= 32:
                k = 10
                im = im.resize((im.size[0] * k, im.size[1] * k), 4)
                im.save("tmp.bmp")
                self.ids.image.source = "tmp.bmp"
            else:
                self.ids.image.source = filename[0]  # str
            self.ids.image.reload()
            self.ids.filechooser._update_files()
            self.box_root.on_btn_sel()
        except Exception:
            self.ids.image.source = "fon.png"

    def update_list(self):
        self.ids.filechooser._update_files()


class Worker(MDBoxLayout):
    """Основной класс"""

    # num = BoundedNumericProperty(None, min=0, max=255)

    def __init__(self, **kvargs):
        super().__init__(**kvargs)
        self.device_name_list = []
        self.serial_port = None
        self.invert_img = False
        self.im = None
        self.err = True
        self.num = None
        self.ids.txt_inp.bind(on_text_validate=self.set_message)
        self.ids.txt_inp.bind(focus=self.on_focus)
        self.ntab = self.sm.get_tabs_list()
        self.name_dev = None
        self.on_btn_scan_release()  #
        self.on_btn_device_release()  #

    def on_tab_switch(self, *args):
        """Обработчик перехода на вкладку Обмен"""
        # print(args[0], args[1], args[2])
        # print(dir(args[1]))
        # print(args[1].children[0].text)  # text вкладки

    def on_stop(self):
        if self.serial_port:
            self.serial_port.close()

    def on_btn_scan_release(self):
        self.box_list.clear_widgets()
        self.device_name_list = []

        if platform == "android":
            usb_device_list = usb.get_usb_device_list()
            self.device_name_list = [
                device.getDeviceName() for device in usb_device_list
            ]
        else:
            usb_device_list = list_ports.comports()
            self.device_name_list = [port.device for port in usb_device_list]
            # self.device_name_list = []

        if self.device_name_list:
            if len(self.device_name_list) == 1:
                self.name_dev = self.device_name_list[0]
            for device_name in self.device_name_list:
                btntext = device_name.center(20)
                # button = Button(text=btntext, size_hint_y=None, height='50sp')
                # button = MDIconButton(text=btntext, pos_hint={"center_x": .5},             ##### MDRoundIconButton
                # font_size="18sp", icon="usb")
                button = MDButton(
                    MDButtonIcon(
                        icon="usb",
                    ),
                    MDButtonText(
                        text=btntext,
                    ),
                    style="elevated",  # "outlined
                    pos_hint={"center_x": 0.5},
                )
                button.bind(on_release=self.on_btn_device_release)
                self.box_list.add_widget(button)
        else:
            label = MDLabel(text="Нет Доступных портов", halign="center")
            self.box_list.add_widget(label)

    def on_btn_device_release(self, btn=None):
        """Кнопка выбора порта"""
        # print(f"> {dir(btn)}")
        if btn is None:
            device_name = self.name_dev
            if device_name is None:
                return
        else:
            # device_name = btn.text.strip()
            device_name = btn._button_text.text.strip()
            # print(device_name)
            # pass
        if self.serial_port is not None:
            return
        if platform == "android":
            device = usb.get_usb_device(device_name)
            if not device:
                raise SerialException(
                    "Устройство {} не пресутствует!".format(device_name)
                )
            if not usb.has_usb_permission(device):
                usb.request_usb_permission(device)
                return
            self.serial_port = serial4a.get_serial_port(
                device_name, 115200, 8, "N", 1, timeout=0.2
            )
        else:
            self.serial_port = Serial(device_name, 115200, 8, "N", 1, timeout=0.2)

        if self.serial_port.is_open:
            self.serial_port.reset_input_buffer()
            self.sm.switch_tab(self.ntab[1])
        else:
            print("Exception")
        # self.sm.switch_tab(self.ntab[1])

    def on_clear_status(self, vol, event):
        """Очистка TextInput и переход на screen vol"""
        self.txt_inp.text = ""
        self.txt_err.text = ""
        self.sm.switch_tab(self.ntab[vol])

    def save_tmp(self, path):
        try:
            im = Image.open(path[0])
            im_ = im
            if self.invert_img:
                im_ = ImageChops.invert(im)
            if im_.size[0] <= 32 or im_.size[1] <= 32:
                k = 20
                im_ = im_.resize((im_.size[0] * k, im_.size[1] * k), 4)
            im_.save("tmp.bmp")
        except:
            im = None
        return im

    def on_btn_sel(self):
        """Переход на вкладку обмен при выборе а filecoser"""
        self.txt_err.text = ""
        path = self.fm.pth
        # print(path)
        if path:
            self.invert_img = False  # !
            self.im = self.save_tmp(path)
            if self.im:
                self.ids.im_prev.source = "tmp.bmp"
                self.ids.im_prev.reload()
                # self.ids.im_prev.source = path[0]
                self.sm.switch_tab(self.ntab[0])  # 2
                self.err = False
                # self.im = Image.open(path[0])
                y = self.im.size[1]
                if y < 8:
                    y = 8
                elif y < 16:
                    y = 16
                elif y < 24:
                    y = 24
                elif y < 32:
                    y = 32
                m = y // 8
                if self.im.size[1] > 32:
                    self.txt_err.text = "Высота марки большая!"
                    self.err = True
                elif self.im.size[0] * m > 253:
                    self.txt_err.text = "Марка большая!"
                    self.err = True
                if self.err:
                    Clock.schedule_once(partial(self.on_clear_status, 1), 3.0)
                    self.ids.im_prev.source = "ne-tak.png"
            else:
                self.txt_err.text = "Не открыть изображение!" ""

    # @staticmethod
    # def bito2(value):
    #     """Перестановка битов в байте"""
    #     value = bin(value)[2:]
    #     return int(value[::-1], 2)

    @staticmethod
    def bit_sw(value):
        """Перестановка битов в байте"""
        b = [0, 0, 0, 0, 0, 0, 0, 0]
        for i in range(8):
            if value & 128:
                b[i] = 1
            value = value << 1
        return (
            128 * b[7]
            + 64 * b[6]
            + 32 * b[5]
            + 16 * b[4]
            + 8 * b[3]
            + 4 * b[2]
            + 2 * b[1]
            + b[0]
        )

    def parse_data(self):
        """Конвертация изображения в формат принтера"""
        out = self.im.transpose(Image.ROTATE_270)
        im2 = out.convert("1")
        if not self.invert_img:
            im2 = ImageChops.invert(im2)
        bs = im2.tobytes()
        bs = [self.bit_sw(i) for i in bs]
        y = divmod(out.size[0] + 7, 8)[0]
        bs.insert(0, len(bs) // y)  # x
        bs.insert(1, y)  # y
        bs.append(0x0D)  # \r
        data = bytearray(bs)
        # print('>>', len(data), data)
        return data

    def head_msg(self, direct=None):
        """Данные номера фрагмента xxx"""
        fr = bytearray(self.txt_inp.text.zfill(3), encoding="latin-1")
        if direct:
            head = b"\x0f\x6c" + fr + b"\x0d"
        else:
            head = b"\x0f\x69" + fr + b"\x0d"
        # print(head)
        return head

    # def checkbox_click(self, instance, value):
    #     """Обработчик флажка инверсии марки"""
    #     self.invert_img = False
    #     if value is True:
    #         self.invert_img = True
    #     if self.im:
    #         path = self.fm.pth
    #         if path:
    #             self.save_tmp(path)
    #             self.ids.im_prev.source = "tmp.bmp"
    #             self.ids.im_prev.reload()

    def inv_img(self):
        """Инверсии марки"""
        if self.im:
            path = self.fm.pth
            if path:
                self.invert_img = not self.invert_img
                self.save_tmp(path)
                self.ids.im_prev.source = "tmp.bmp"
                self.ids.im_prev.reload()

    def on_focus(self, instans, v):
        """ "Сработает при смене фокуса v=True есть фокус False нет"""
        # print(f'{v}')
        if not v:
            self.set_message()

    def set_message(self, *args):
        """Получить значение из TextField по Enter или потери фокуса"""
        n = self.txt_inp.text
        if not n:
            return
        try:
            self.num = int(n)
            self.txt_err.text = ""
        except Exception:
            self.txt_err.text = "Ошибка!"
            self.num = None
            # Clock.schedule_once(partial(self.on_clear_status, 2), 1.5)
            # print(er)

    def on_btn_load(self):
        """Загрузка марки в принтер 0x0f, 0x6c, xxx, 0x0d, x, y, data, 0x0d"""
        if not self.serial_port:
            self.txt_err.text = "Не выбран порт!"
            Clock.schedule_once(partial(self.on_clear_status, 2), 1.5)
            return
        if not self.im or self.err:
            # print(f">>{self.im}, {self.err}")
            self.txt_err.text = "Не выбрана марка!"
            Clock.schedule_once(partial(self.on_clear_status, 1), 1.0)
            return
        if self.num is None:
            self.txt_err.text = "Не выбран фрагмент!"
            return
        if self.num > 247:  # 127
            self.txt_err.text = "Много!"
            # Clock.schedule_once(partial(self.on_clear_status, 2), 1.0)
            return
        if self.serial_port.is_open:
            head = self.head_msg(1)
            data = self.parse_data()
            self.serial_port.write(head)
            time.sleep(2e-05)
            self.serial_port.write(data)
            self.txt_err.text = f"Загружено в {self.num}"
            self.txt_inp.text = ""
            self.num = None
            self.ids.im_prev.source = "tmp.bmp"
            # Clock.schedule_once(partial(self.on_clear_status, 2), 2)
            # print(self.invert_img)

    def on_btn_read(self):
        """Чтение марки из принтера 0x0f, 0x6c, xxx, 0x0d"""
        req = self.head_msg()
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.reset_input_buffer()
            self.serial_port.write(req)
            time.sleep(2e-05)
            self.recieve()
            self.fm.update_list()
        else:
            self.txt_err.text = "Не выбран порт!"
            Clock.schedule_once(partial(self.on_clear_status, 2), 1.5)
        self.invert_img = False  # !
        # self.cb.active = False  # !
        # self.im = None
        # self.ids.im_prev.source = "fon.png"

    def recieve(self):
        """Прием данных о марке N, x, y, data"""
        col_bytes = self.serial_port.read(1)  # bytes
        # print(col_bytes)        # b'\xef' ????? на COM1
        if col_bytes:
            len_int = int.from_bytes(col_bytes, byteorder="big")  # int
            buf = self.serial_port.read(len_int)
            if len(buf) != len_int:
                self.txt_err.text = "Ошибка!"
                self.ids.im_prev.source = "ne-tak.png"
                self.im = None
                # Clock.schedule_once(partial(self.on_clear_status, 2), 1.5)
                return
            x, y = buf[0], buf[1]
            bn = [self.bit_sw(i) for i in buf[2:]]
            # print(x, y, len(bn))
            _path = os.path.join(primary_ext_storage, "mapimg")
            fr = self.txt_inp.text.zfill(3)
            outfile = os.path.join(_path, f"{fr}.bmp")
            # print(outfile)
            try:
                im_ = Image.frombytes("1", (y * 8, x), bytes(bn))
                im_ = im_.transpose(Image.ROTATE_90)
                im_ = ImageChops.invert(im_)
                im_.save(outfile)
                if im_.size[0] <= 32 or im_.size[1] <= 32:
                    k = 20
                    im_ = im_.resize((im_.size[0] * k, im_.size[1] * k), 4)
                im_.save("tmp.bmp")
                self.im = im_
                self.ids.im_prev.source = "tmp.bmp"
                self.ids.im_prev.reload()
                self.txt_err.text = f"Прочитано из {self.txt_inp.text}"
            except:
                self.txt_inp.text = "Не прочитано"
                # Clock.schedule_once(partial(self.on_clear_status, 0), 1.5)
                self.im = None
        else:
            self.txt_err.text = "Фрагмент пуст"
            self.ids.im_prev.source = "fon.png"
            self.im = None

    def on_btn_exit(self):
        """Выход"""
        try:
            os.remove("tmp.bmp")
        except OSError:
            pass
        self.on_stop()
        sys.exit(0)


# class IconListItem(OneLineIconListItem):
#     left_icon = StringProperty()


class Markap2App(MDApp):
    title = "Маркировочные аппараты"
    # icon = "print.png"

    def build(self):
        self.icon = "print.png"
        # self.theme_cls.theme_style = "Dark"
        # self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Green"
        self.theme_cls.primary_hue = 500

        # self.s = Worker()
        menu_items = [
            {
                # "viewclass": "IconListItem",  # "OneLineListItem"
                "text": "Порт",
                # "left_icon": "page-next-outline",
                "leading_icon": "usb",
                "height": dp(40),
                "on_release": lambda x="0": self.menu_callback(x),
            },
            {
                # "viewclass": "IconListItem",  # "OneLineListItem"
                "text": "Выбор",
                # "left_icon": "page-next-outline",
                "leading_icon": "cursor-default-click",
                "height": dp(40),
                "on_release": lambda x="1": self.menu_callback(x),
            },
            {
                # "viewclass": "IconListItem",  # "OneLineListItem"
                "text": "Обмен",
                # "left_icon": "page-next-outline",
                "leading_icon": "upload",
                "height": dp(40),
                "on_release": lambda x="2": self.menu_callback(x),
            },
            {
                # "viewclass": "IconListItem",  # "OneLineListItem"
                "text": "Выход",
                # "left_icon": "exit-run",  # exit-to-app
                "leading_icon": "exit-to-app",
                "height": dp(40),
                "on_release": lambda x="exit": self.menu_callback(x),
            },
        ]
        self.menu = MDDropdownMenu(
            items=menu_items,
            # width_mult=3,
            # radius=[dp(5)],
            # background_color=(0.3, 0.3, 0.3, 0.5),
            position="bottom",
        )
        menu_items_2 = [
            {
                "text": "Инверсия",
                "leading_icon": "invert-colors",
                "height": dp(40),
                "on_release": lambda x="0": self.menu_callback_2(x),
            },
            {
                "text": "Сменить тему",
                "leading_icon": "theme-light-dark",
                "height": dp(40),
                "on_release": lambda: self.switch_theme(),
            },
            {
                "text": "Выход",
                "leading_icon": "exit-to-app",
                "height": dp(40),
                "on_release": lambda x="exit": self.menu_callback(x),
            },
        ]

        self.menu_2 = MDDropdownMenu(
            items=menu_items_2,
            position="bottom",
        )
        pt = os.path.join(primary_ext_storage, "mapimg")
        if not os.path.exists(pt):
            os.mkdir(os.path.join(pt))
        # return self.s
        self.s = Worker()
        self.screen = MDScreen(
            self.s,
            md_bg_color=self.theme_cls.backgroundColor,
        )
        # return MDScreen(
        #     self.s,
        #     md_bg_color=self.theme_cls.backgroundColor,
        # )
        return self.screen

    def switch_theme(self):
        self.menu_2.dismiss()
        # self.theme_cls.theme_style = (
        #     "Dark" if self.theme_cls.theme_style == "Light" else "Light"
        # )
        self.theme_cls.switch_theme()

        self.screen.md_bg_color = self.theme_cls.backgroundColor

    def callback(self, button=None):
        """Обработчик левого меню"""
        self.menu.caller = self.s.button
        self.menu.open()

    def menu_callback(self, x):
        self.menu.dismiss()
        if x == "0":
            self.s.sm.switch_tab(self.s.ntab[2])
        elif x == "1":
            self.s.sm.switch_tab(self.s.ntab[1])
        elif x == "2":
            self.s.sm.switch_tab(self.s.ntab[0])
        else:
            self.s.on_btn_exit()

    def change_actions_items(self, button=None):
        """Обработчик  правого меню"""
        self.menu_2.caller = self.s.button_2
        self.menu_2.open()

    def menu_callback_2(self, x):
        self.menu_2.dismiss()
        self.s.inv_img()

    def on_stop(self):
        self.s.on_stop()

    def on_pause(self):
        return True


if __name__ == "__main__":
    Markap2App().run()
"""
‘Red’, ‘Pink’, ‘Purple’, ‘DeepPurple’, ‘Indigo’, ‘Blue’, 
‘LightBlue’, ‘Cyan’, ‘Teal’, ‘Green’, ‘LightGreen’, ‘Lime’, 
‘Yellow’, ‘Amber’, ‘Orange’, ‘DeepOrange’, ‘Brown’, ‘Gray’, 
‘BlueGray’
"""
