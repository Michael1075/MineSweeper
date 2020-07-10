#!/usr/bin/env python3
# coding: utf-8

from cython_ext.ext import PyConsoleTools


__author__ = "Michael W"
COPYRIGHT_STR = "autosweeper.py - by {0}".format(__author__)


CONSOLE = PyConsoleTools()


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
        CONSOLE.print_with_color(InputTools.WRONG_INPUT_MSG + "\n", color=0x0c)
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
        print(base_prompt)
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
