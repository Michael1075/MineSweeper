#!/usr/bin/env python3
# coding: utf-8

# website: https://github.com/Michael1075/autosweeper

from cython_ext import py_main
from cython_ext import PyConsoleTools


__author__ = "Michael W"
COPYRIGHT_STR = "cy_autosweeper.py - by {0}".format(__author__)


CONSOLE = PyConsoleTools()


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
        CONSOLE.printf_with_color(InputTools.WRONG_INPUT_MSG, color=0x0c)
        print()
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
            "{0:>" + str(len(str(longest_index_num))) + "}"
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


class Prompt(object):
    HINT = "\n".join([
        "Hint: When typing in parameters, you can type nothing and directly",
        "get the default value marked with '[]'."
    ])
    MAP_WIDTH = "Please input the width of the map."
    MAP_HEIGHT = "Please input the height of the map."
    NUM_MINES = "Please input the number of mines."
    NUM_GAMES = "Please input times that the game should be played for."
    RECORD_MODE = "\n".join([
        "Please choose a record mode to determine whether each game will be",
        "recorded."
    ])
    NUM_RECORDED_GAMES = "How many games shall be recorded (1 at least)?"
    UPDATE_FREQ = "After how many games should the statistics data be updated?"


class ChoicesPrompts(object):
    RECORD_MODE = (
        "No recordings",
        "Record all games",
        "Record only won games",
        "Record only lost games",
        "Record some best-played games"
    )


class MainProcess(object):
    @staticmethod
    def __init__():
        CONSOLE.set_console_size_to_default()
        CONSOLE.clear_console()
        print(COPYRIGHT_STR)
        MainProcess.input_parameters_and_run()

    @staticmethod
    def input_specification():
        map_width = InputTools.assertion_input(
            int, Prompt.MAP_WIDTH, 30, lambda x: x > 0
        )
        map_height = InputTools.assertion_input(
            int, Prompt.MAP_HEIGHT, 16, lambda x: x > 0
        )
        num_mines = InputTools.assertion_input(
            int, Prompt.NUM_MINES, 99, lambda x: x > 0
        )
        return map_width, map_height, num_mines

    @staticmethod
    def input_sleep_per_step(default_time):
        sleep_per_step = InputTools.assertion_input(
            float, Prompt.SLEEP_PER_STEP, default_time, lambda x: x >= 0.0
        )
        return sleep_per_step

    @staticmethod
    def input_sleep_per_game(default_time):
        sleep_per_game = InputTools.assertion_input(
            float, Prompt.SLEEP_PER_GAME, default_time, lambda x: x >= 0.0
        )
        return sleep_per_game

    @staticmethod
    def handle():
        map_width, map_height, num_mines = MainProcess.input_specification()
        num_games = InputTools.assertion_input(
            int, Prompt.NUM_GAMES, 1000, lambda x: x > 0
        )
        record_mode = InputTools.prompts_input(
            Prompt.RECORD_MODE, 0, ChoicesPrompts.RECORD_MODE
        )
        if record_mode == 4:
            num_recorded_games = InputTools.assertion_input(
                int, Prompt.NUM_RECORDED_GAMES, 1, lambda x: 0 < x <= num_games
            )
            record_mode = -num_recorded_games
        update_freq_default_val = num_games // 100
        if update_freq_default_val == 0:
            update_freq_default_val = 1
        update_freq = InputTools.assertion_input(
            int, Prompt.UPDATE_FREQ, update_freq_default_val, lambda x: x > 0
        )
        py_main(
            map_width, map_height, num_mines,
            num_games, record_mode, update_freq
        )

    @staticmethod
    def input_parameters_and_run():
        CONSOLE.printf_with_color(Prompt.HINT, color=0x0a)
        print()
        MainProcess.handle()


if __name__ == "__main__":
    MainProcess()
