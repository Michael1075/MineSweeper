#!/usr/bin/env python3
# coding: utf-8

# website: https://github.com/Michael1075/autosweeper

import json
import os
import time

from cython_ext.ext import PyInterface
from cy_tools import *


__author__ = "Michael W"


class GameRecorder(object):
    FOLDER_NAME = "game_savings"

    def __init__(self, game):
        self.map_width = game.map_width
        self.map_height = game.map_height
        self.num_mines = game.num_mines
        self.game_status = game.game_status
        self.progress = game.num_boxes - game.num_unknown_boxes
        self.num_flags = game.num_mines - game.num_unknown_mines
        self.num_steps = game.num_steps
        self.num_guesses = game.num_random_steps
        self.time_used = game.time_used
        self.mine_indexes = game.mine_indexes
        self.step_index_list = game.step_index_list
        self.step_mode_list = game.step_mode_list

    def get_json_dict(self):
        time_used_str = "{0} ms".format(
            StringTools.set_decimal(6).format(self.time_used * 1e3)
        )
        return {
            "map_width": str(self.map_width),
            "map_height": str(self.map_height),
            "num_mines": str(self.num_mines),
            "game_result": "won" if self.game_status == 2 else "lost",
            "progress": str(self.progress),
            "num_flags": str(self.num_flags),
            "num_steps": str(self.num_steps),
            "num_guesses": str(self.num_guesses),
            "time_used": time_used_str,
            "mine_indexes": " ".join(map(str, self.mine_indexes)),
            "step_indexes": " ".join(map(str, self.step_index_list)),
            "step_mode_nums": "".join(map(str, self.step_mode_list)),
        }

    def record(self):
        json_dict = self.get_json_dict()
        folder_name = "-".join(map(str, (
            self.map_width, self.map_height, self.num_mines
        )))
        folder_path = os.path.join(GameRecorder.FOLDER_NAME, folder_name)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        filename = str(len(os.listdir(folder_path))) + ".json"
        file_path = os.path.join(folder_path, filename)
        with open(file_path, "w") as output_file:
            json.dump(json_dict, output_file, indent=0)


class Interface(object):
    def __init__(self, map_width, map_height, num_mines,
            display_mode, record_mode, sleep_per_step_if_displayed):
        self._c_interface = PyInterface(map_width, map_height, num_mines,
            display_mode, record_mode, sleep_per_step_if_displayed)
        for attr_name in (
            "map_width", "map_height", "num_mines", "num_boxes",
            "display_mode", "record_mode", "sleep_per_step_if_displayed",
            "console_cols", "console_lines"
        ):
            self.__dict__[attr_name] = eval("self._c_interface." + attr_name)

    def __getattr__(self, attr_name):
        if attr_name in (
            "num_unknown_boxes", "num_unknown_mines", "mine_indexes",
            "game_status", "num_steps", "num_random_steps", "time_used",
            "step_index_list", "step_mode_list"
        ):
            return eval("self._c_interface." + attr_name)

    def re_initialize(self):
        self._c_interface.re_initialize()

    def prepare_console(self, cols, lines):
        self._c_interface.prepare_console(cols, lines)

    def begin_process(self):
        self.prepare_console(self.console_cols, self.console_lines)

    def run(self):
        self._c_interface.run()

    def terminate_process(self):
        self._c_interface.terminate_process()

    def get_recorder(self):
        return GameRecorder(self)

    def record_game_data(self):
        recorder = self.get_recorder()
        recorder.record()


class GameStatistics(Interface):
    STATISTICS_TITLE = "- Statistics -"
    STATISTICS_KEYS = (
        "Specification", "Main progress", "Games won", "Without guesses",
        "Avg. progress", "Avg. flags", "Avg. steps", "Avg. steps (won)",
        "Avg. guesses", "Avg. time", "Avg. time (won)"
    )
    KEY_VAL_SEPARATOR = " "

    def __init__(self, map_width, map_height, num_mines, num_games,
            display_mode, record_mode, update_freq,
            sleep_per_step_if_displayed, sleep_per_game_if_displayed):
        Interface.__init__(
            self, map_width, map_height, num_mines,
            display_mode, record_mode, sleep_per_step_if_displayed
        )
        self.num_games = num_games
        self.update_freq = update_freq
        self.sleep_per_game_if_displayed = sleep_per_game_if_displayed

        self.num_games_won = 0
        self.num_games_won_without_guesses = 0
        self.progress_list = [0] * num_games
        self.num_flags_list = [0] * num_games
        self.num_steps_list = [0] * num_games
        self.num_won_games_steps_list = [0] * num_games
        self.num_random_steps_list = [0] * num_games
        self.time_list = [0.0] * num_games
        self.won_games_time_list = [0.0] * num_games
        if record_mode < 0:
            self.num_recorded_games = -record_mode
        else:
            self.num_recorded_games = 0
        self.ranking_list = []

        self.key_info_width = 0
        self.value_info_width = 0
        self.statistic_info_width = 0
        self.init_statistics_params()

    def init_statistics_params(self):
        num_games = self.num_games
        num_boxes = self.num_boxes
        num_mines = self.num_mines
        max_time = 1e4
        longest_statistics_values = self.get_statistics_values_template(
            num_games, num_games, num_games, num_boxes, num_mines,
            num_boxes, num_boxes, num_boxes, max_time, max_time
        )
        statistic_info_height = len(GameStatistics.STATISTICS_KEYS)
        assert statistic_info_height == len(longest_statistics_values)
        self.key_info_width = max(map(len, GameStatistics.STATISTICS_KEYS))
        self.value_info_width = max(map(len, longest_statistics_values))
        statistic_info_width = self.key_info_width \
            + len(GameStatistics.KEY_VAL_SEPARATOR) + self.value_info_width
        assert len(GameStatistics.STATISTICS_TITLE) <= statistic_info_width
        self.statistic_info_width = statistic_info_width
        self.console_cols = max(self.console_cols, statistic_info_width)
        self.console_lines += statistic_info_height + 1

    def get_statistics_values_template(self, serial_num, num_games_won,
            num_games_won_without_guesses, avg_progress, avg_num_flags,
            avg_num_steps, avg_won_games_num_steps, avg_num_random_steps,
            avg_time, avg_won_games_time):
        return (
            "{0} * {1} / {2} ({3})".format(
                self.map_width, self.map_height, self.num_mines,
                StringTools.set_percentage(2).format(
                    f_div(self.num_mines, self.num_boxes)
                )
            ),
            "{0} / {1} ({2})".format(
                serial_num, self.num_games,
                StringTools.set_percentage(2).format(
                    f_div(serial_num, self.num_games)
                )
            ),
            "{0} / {1} ({2})".format(
                num_games_won, serial_num,
                StringTools.set_percentage(2).format(
                    f_div(num_games_won, serial_num)
                )
            ),
            "{0} / {1} ({2})".format(
                num_games_won_without_guesses, serial_num,
                StringTools.set_percentage(2).format(
                    f_div(num_games_won_without_guesses, serial_num)
                )
            ),
            "{0} / {1} ({2})".format(
                StringTools.set_decimal(3).format(avg_progress),
                self.num_boxes,
                StringTools.set_percentage(2).format(
                    f_div(avg_progress, self.num_boxes)
                )
            ),
            "{0} / {1} ({2})".format(
                StringTools.set_decimal(3).format(avg_num_flags),
                self.num_mines,
                StringTools.set_percentage(2).format(
                    f_div(avg_num_flags, self.num_mines)
                )
            ),
            "{0} step(s)".format(
                StringTools.set_decimal(3).format(avg_num_steps)
            ),
            "{0} step(s)".format(
                StringTools.set_decimal(3).format(avg_won_games_num_steps)
            ),
            "{0} step(s)".format(
                StringTools.set_decimal(3).format(avg_num_random_steps)
            ),
            "{0} ms".format(
                StringTools.set_decimal(6).format(avg_time * 1e3)
            ),
            "{0} ms".format(
                StringTools.set_decimal(6).format(avg_won_games_time * 1e3)
            ),
        )

    def get_statistics_values(self, serial_num):
        num_games_won = self.num_games_won
        avg_progress = f_div(sum(self.progress_list), serial_num)
        avg_num_flags = f_div(sum(self.num_flags_list), serial_num)
        avg_num_steps = f_div(sum(self.num_steps_list), serial_num)
        avg_won_games_num_steps = f_div(
            sum(self.num_won_games_steps_list), num_games_won
        )
        avg_num_random_steps = f_div(
            sum(self.num_random_steps_list), serial_num
        )
        avg_time = f_div(sum(self.time_list), serial_num)
        avg_won_games_time = f_div(sum(self.won_games_time_list), num_games_won)
        return self.get_statistics_values_template(
            serial_num, num_games_won,
            self.num_games_won_without_guesses, avg_progress, avg_num_flags,
            avg_num_steps, avg_won_games_num_steps,
            avg_num_random_steps, avg_time, avg_won_games_time
        )

    def get_statistics_begin_line_index(self):
        if self.display_mode == 3:
            return 2
        if self.display_mode == 2:
            return 5
        return self.map_height + 7

    def print_statistics_keys(self):
        begin_line_index = self.get_statistics_begin_line_index()
        CONSOLE.print_in_line(
            begin_line_index - 1,
            StringTools.set_space(self.statistic_info_width, 0).format(
                GameStatistics.STATISTICS_TITLE
            )
        )
        for line_index, statistics_key in enumerate(
            GameStatistics.STATISTICS_KEYS
        ):
            CONSOLE.print_in_line(
                begin_line_index + line_index,
                StringTools.set_space(self.key_info_width, -1).format(
                    statistics_key
                ) + GameStatistics.KEY_VAL_SEPARATOR
            )

    def print_statistics_values(self, serial_num):
        statistics_values = self.get_statistics_values(serial_num)
        begin_line_index = self.get_statistics_begin_line_index()
        begin_col_index = self.key_info_width \
            + len(GameStatistics.KEY_VAL_SEPARATOR)
        for line_index, statistics_val in enumerate(statistics_values):
            CONSOLE.print_at(
                (begin_col_index, begin_line_index + line_index),
                StringTools.set_space(self.value_info_width, 1).format(
                    statistics_val
                )
            )

    def update_statistics_data(self, game, game_index):
        if game.game_status == 2:
            self.num_games_won += 1
            if game.num_random_steps == 0:
                self.num_games_won_without_guesses += 1
            self.num_won_games_steps_list[game_index] = game.num_steps
            self.won_games_time_list[game_index] = game.time_used
        self.progress_list[game_index] \
            = game.num_boxes - game.num_unknown_boxes
        self.num_flags_list[game_index] \
            = game.num_mines - game.num_unknown_mines
        self.num_steps_list[game_index] = game.num_steps
        self.num_random_steps_list[game_index] = game.num_random_steps
        self.time_list[game_index] = game.time_used
        serial_num = game_index + 1
        if serial_num % self.update_freq == 0 or serial_num == self.num_games:
            self.print_statistics_values(serial_num)

    def update_ranking_list(self, game):
        if not self.num_recorded_games:
            return
        game_recorder = game.get_recorder()
        if game.num_unknown_boxes == 0:
            game_recorder.record()
            self.num_recorded_games -= 1
        else:
            self.ranking_list.append((game.num_unknown_boxes, game_recorder))
            self.ranking_list.sort(key=lambda pair: pair[0])
        if len(self.ranking_list) > self.num_recorded_games:
            self.ranking_list.pop()

    def begin_process(self):
        Interface.begin_process(self)
        self.print_statistics_keys()
        self.print_statistics_values(0)

    def run_whole_process(self):
        self.begin_process()
        game = Interface(
            self.map_width, self.map_height, self.num_mines,
            self.display_mode, self.record_mode,
            self.sleep_per_step_if_displayed
        )
        for game_index in range(self.num_games):
            if game_index > 0:
                time.sleep(self.sleep_per_game_if_displayed)
            game.run()
            self.update_statistics_data(game, game_index)
            self.update_ranking_list(game)
            game.re_initialize()
        for pair in self.ranking_list:
            game_recorder = pair[1]
            game_recorder.record()
        self.terminate_process()


class Prompt(object):
    HINT = "\n".join([
        "Hint: When typing in parameters, you can type nothing and directly",
        "get the default value marked with '[]'."
    ])
    MAP_WIDTH = "Please input the width of the map."
    MAP_HEIGHT = "Please input the height of the map."
    NUM_MINES = "Please input the number of mines."
    NUM_GAMES = "Please input times that the game should be played for."
    FILE_ID = "Please input the file-id of the game to be displayed."
    DISPLAY_MODE = "\n".join([
        "Please choose a display mode to determine how each game will be",
        "displayed (1 is recommended if the map is too large)."
    ])
    RECORD_MODE = "\n".join([
        "Please choose a record mode to determine whether each game will be",
        "recorded."
    ])
    NUM_RECORDED_GAMES = "How many games shall be recorded (1 at least)?"
    UPDATE_FREQ = "After how many games should the statistics data be updated?"
    SLEEP_PER_STEP = "How long shall the computer sleep after each step?"
    SLEEP_PER_GAME = "How long shall the computer sleep after each game?"


class ChoicesPrompts(object):
    DISPLAY_MODE = (
        "Display the map and basic information after each step",
        "Display the map after each step",
        "Display basic information at the end of each game",
        "Only display the statistics data"
    )
    RECORD_MODE = (
        "No recordings",
        "Record all games",
        "Record only won games",
        "Record only lost games",
        "Record some best-played games"
    )


class MainProcess(object):
    def __init__(self):
        CONSOLE.set_console_size_to_default()
        CONSOLE.print_copyright_str()
        print()
        process = self.input_parameters()
        process.run_whole_process()

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

    def handle(self):
        map_width, map_height, num_mines = MainProcess.input_specification()
        num_games = InputTools.assertion_input(
            int, Prompt.NUM_GAMES, 1000, lambda x: x > 0
        )
        display_mode = InputTools.prompts_input(
            Prompt.DISPLAY_MODE, 3, ChoicesPrompts.DISPLAY_MODE
        )
        record_mode = InputTools.prompts_input(
            Prompt.RECORD_MODE, 0, ChoicesPrompts.RECORD_MODE
        )
        if record_mode == 4:
            num_recorded_games = InputTools.assertion_input(
                int, Prompt.NUM_RECORDED_GAMES, 1, lambda x: 0 < x <= num_games
            )
            record_mode = -num_recorded_games
        update_freq = InputTools.assertion_input(
            int, Prompt.UPDATE_FREQ, 100, lambda x: x > 0
        )
        if display_mode != 3:
            sleep_per_step = MainProcess.input_sleep_per_step(0.0)
            sleep_per_game = MainProcess.input_sleep_per_game(0.0)
        else:
            sleep_per_step = 0.0
            sleep_per_game = 0.0
        return GameStatistics(
            map_width, map_height, num_mines, num_games,
            display_mode, record_mode, update_freq,
            sleep_per_step, sleep_per_game
        )

    def input_parameters(self):
        CONSOLE.print_with_color(Prompt.HINT + "\n", color=0x0a)
        process = self.handle()
        return process


if __name__ == "__main__":
    MainProcess()
