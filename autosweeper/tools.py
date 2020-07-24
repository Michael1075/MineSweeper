#!/usr/bin/env python3
# coding: utf-8

import ctypes
import os
import sys


__author__ = "Michael W"
COPYRIGHT_STR = "autosweeper.py - by {0}".format(__author__)


def print_(value):
    print(value, end="", flush=True)


def f_div(a, b):
    try:
        return a / b
    except ZeroDivisionError:
        return 0.0


class StringTools(object):
    @staticmethod
    def set_space(str_length, align, *, str_index=0):
        """
        :param align: int in range(-1, 2)
            -1: align at left side
            0: align at center
            1: align at right side
        """
        if align == 1:
            align_mark = ">"
        elif align == 0:
            align_mark = "^"
        else:
            align_mark = "<"
        return "{" + str(str_index) + ":" + align_mark + str(str_length) + "}"
    
    @staticmethod
    def set_decimal(decimal, *, str_index=0):
        return "{" + str(str_index) + ":." + str(decimal) + "f}"
    
    @staticmethod
    def set_percentage(decimal, *, str_index=0):
        return "{" + str(str_index) + ":." + str(decimal) + "%}"


class InputTools(object):
    WRONG_INPUT_MSG = "Wrong input!"
    INPUT_AGAIN_PROMPT = "Please input again: "

    @staticmethod
    def input_with_default_val(prompt, default_val):
        val = input(prompt)
        if not val:
            val = default_val
        return val

    @staticmethod
    def input_again(default_val):
        ConsoleTools.print_with_color(InputTools.WRONG_INPUT_MSG, color=0x0c)
        ConsoleTools.put_new_line()
        return InputTools.input_with_default_val(
            InputTools.INPUT_AGAIN_PROMPT, default_val
        )

    @staticmethod
    def check_input(data_cls, val, assert_func):
        try:
            result = data_cls(val)
        except ValueError:
            return False
        return assert_func(result)

    @staticmethod
    def input_loop(data_cls, base_prompt, prompt, default_val, assert_func):
        print_(base_prompt)
        ConsoleTools.put_new_line()
        val = InputTools.input_with_default_val(prompt, default_val)
        while not InputTools.check_input(data_cls, val, assert_func):
            val = InputTools.input_again(default_val)
        return data_cls(val)

    @staticmethod
    def assertion_input(data_cls, base_prompt, default_val, assert_func):
        suffix = "[{0}]: ".format(default_val)
        return InputTools.input_loop(
            data_cls, base_prompt, suffix, default_val, assert_func
        )

    @staticmethod
    def choices_input(data_cls, base_prompt, default_val, choices):
        def assert_func(x):
            return x in choices
        choices_str = list(map(str, choices))
        choices_str[choices.index(default_val)] = "[{0}]".format(default_val)
        suffix = "/".join(choices_str)
        suffix = "({0}): ".format(suffix)
        return InputTools.input_loop(
            data_cls, base_prompt, suffix, default_val, assert_func
        )

    @staticmethod
    def prompts_input(base_prompt, default_val, choices_prompts):
        choices = list(range(len(choices_prompts)))
        longest_index_num = len(choices_prompts) - 1
        index_num_template = " - {0}. ".format(
            StringTools.set_space(len(str(longest_index_num)), 1)
        )
        longest_index_num_str = index_num_template.format(
            longest_index_num
        )
        formatted_prompts = [base_prompt]
        for choice_num, choice_prompt in enumerate(choices_prompts):
            prompt_tail = "." if choice_num == longest_index_num else ";"
            formatted_prompts.append(
                index_num_template.format(choice_num) + choice_prompt.replace(
                    "\n", "\n" + len(longest_index_num_str) * " "
                ) + prompt_tail
            )
        base_prompt = "\n".join(formatted_prompts)
        return InputTools.choices_input(
            int, base_prompt, default_val, choices
        )


class ConsoleCursor(object):
    STD_INPUT_HANDLE = -10
    STD_OUTPUT_HANDLE = -11
    STD_ERROR_HANDLE = -12
    HANDLE_STD_OUT = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)


class ConsoleCursorInfo(ctypes.Structure, ConsoleCursor):
    _fields_ = [("dwSize", ctypes.c_int), ("bVisible", ctypes.c_int)]
    DEFAULT_DW_SIZE = 20

    def __init__(self, visible):
        self.dwSize = ConsoleCursorInfo.DEFAULT_DW_SIZE
        self.bVisible = visible
        ctypes.windll.kernel32.SetConsoleCursorInfo(
            ConsoleCursor.HANDLE_STD_OUT, ctypes.byref(self)
        )


class ConsoleCursorPosition(ctypes.Structure, ConsoleCursor):
    _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]

    def __init__(self, x, y):
        self.X = x
        self.Y = y
        ctypes.windll.kernel32.SetConsoleCursorPosition(
            ConsoleCursor.HANDLE_STD_OUT, self
        )


class ConsoleTextColor(ConsoleCursor):
    def __init__(self, color):
        """
        :param color: hex int
            The two digits indicate the foreground color and the background
            color respectively.

            0: black
            1: dark blue
            2: dark green
            3: dark blue
            4: dark red
            5: dark pink
            6: dark yellow
            7: dark white
            8: dark gray
            9: blue
            a: green
            b: blue
            c: red
            d: pink
            e: yellow
            f: white
        """
        ctypes.windll.kernel32.SetConsoleTextAttribute(
            ConsoleCursor.HANDLE_STD_OUT, color
        )


class ConsoleTools(object):
    DEFAULT_CONSOLE_COLS = 80
    DEFAULT_CONSOLE_LINES = 40

    def __init__(self):
        self.__cols = ConsoleTools.DEFAULT_CONSOLE_COLS
        self.__lines = ConsoleTools.DEFAULT_CONSOLE_COLS

    @staticmethod
    def clear_console():
        os.system("cls")

    @staticmethod
    def hide_cursor():
        ConsoleCursorInfo(0)

    @staticmethod
    def show_cursor():
        ConsoleCursorInfo(1)

    @staticmethod
    def __set_cmd_text_color(color):
        ConsoleTextColor(color)

    @staticmethod
    def __reset_color():
        ConsoleTools.__set_cmd_text_color(0x0f)

    @staticmethod
    def put_new_line():
        print_("\n")

    @staticmethod
    def print_with_color(value, *, color):
        ConsoleTools.__set_cmd_text_color(color)
        print_(value)
        ConsoleTools.__reset_color()

    def __set_console_size(self):
        os.system("mode con cols={0} lines={1}".format(
            self.__cols + 3, self.__lines + 2
        ))
    
    def set_console_size(self, cols, lines):
        self.__cols = cols
        self.__lines = lines
        self.__set_console_size()
    
    def set_console_size_to_default(self):
        self.__init__()
        self.__set_console_size()

    def __move_cursor_to(self, coord):
        x, y = coord
        assert x < self.__cols and y < self.__lines
        ConsoleCursorPosition(x, y)

    def move_cursor_to_line(self, line_index):
        self.__move_cursor_to((0, line_index))

    def move_cursor_to_end_line(self, reversed_line_index):
        self.move_cursor_to_line(self.__lines - reversed_line_index - 1)

    def print_at(self, coord, value, *, color=0x0f):
        assert "\n" not in value
        assert len(value) + coord[0] <= self.__cols
        self.__move_cursor_to(coord)
        ConsoleTools.print_with_color(value, color=color)

    def print_in_line(self, line_index, value, *, color=0x0f):
        self.print_at((0, line_index), value, color=color)

    def print_list_as_table_row(self, line_index, list_obj,
            cell_width, align, cell_separator):
        cell_str_template_list = [
            StringTools.set_space(cell_width, align, str_index=k)
            for k in range(len(list_obj))
        ]
        self.print_in_line(
            line_index,
            cell_separator.join(cell_str_template_list).format(*list_obj)
        )

    def print_copyright_str(self):
        self.print_in_line(0, COPYRIGHT_STR)

    @staticmethod
    def pause():
        print_("Press any key to quit...")
        os.system(" ".join(("pause", ">", os.devnull)))

    def ready_to_begin(self, cols, lines):
        ConsoleTools.clear_console()
        ConsoleTools.hide_cursor()
        ConsoleTools.__reset_color()
        self.set_console_size(cols, lines)

    def ready_to_quit(self):
        ConsoleTools.show_cursor()
        self.move_cursor_to_end_line(0)
        ConsoleTools.pause()
        ConsoleTools.clear_console()
        self.set_console_size_to_default()
        sys.exit()
