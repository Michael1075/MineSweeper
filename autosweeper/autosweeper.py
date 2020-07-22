#!/usr/bin/env python3
# coding: utf-8

# website: https://github.com/Michael1075/autosweeper

from abc import abstractmethod
import json
import os
import random
import time

from tools import *


__author__ = "Michael W"


CONSOLE = ConsoleTools()


class Core(object):
    def __init__(self, map_width, map_height, num_mines):
        """
        :attr game_status: int in range(4)
            0: preparing
            1: processing
            2: won
            3: lost

        :attr step_mode: int in range(4)
            0: explore
            1: explore_surrounding
            2: flag
            3: guess

        :attr view_map: list[int in range(14)]
            0~8: numbers
            9: blank
            10: flag
            11: exploded mine
            12: mine that hasn't been flagged
            13: safe box that has been wrongly flagged
        """
        self.map_width = map_width
        self.map_height = map_height
        self.num_mines = num_mines
        self.num_boxes = num_boxes = map_width * map_height
        self.num_unknown_boxes = num_boxes
        self.num_unknown_mines = num_mines
        self.mine_indexes = [-1] * num_mines
        self.base_map = [0] * num_boxes
        self.view_map = [9] * num_boxes

        self.game_status = 0
        self.num_steps = 0
        self.num_random_steps = 0
        self.previous_index = 0
        self.time_used = 0.0

        self.surrounding_indexes = [[]] * num_boxes
        self.sub_surrounding_indexes = [[]] * num_boxes
        self.init_surrounding_indexes()

    def init_surrounding_indexes(self):
        for i in range(self.num_boxes):
            self.surrounding_indexes[i] = self.get_surrounding_indexes(i)
            self.sub_surrounding_indexes[i] = self.get_surrounding_indexes(
                i, layer=2
            )

    def re_initialize(self):
        self.num_unknown_boxes = self.num_boxes
        self.num_unknown_mines = self.num_mines
        self.mine_indexes = [-1] * self.num_mines
        self.base_map = [0] * self.num_boxes
        self.view_map = [9] * self.num_boxes

        self.game_status = 0
        self.num_steps = 0
        self.num_random_steps = 0
        self.previous_index = 0
        self.time_used = 0.0

    @staticmethod
    def get_union(list0, list1):
        return [e for e in list0 if e in list1]

    @staticmethod
    def get_difference(list0, list1):
        return [e for e in list0 if e not in list1]

    def coord_to_index(self, coord):
        x, y = coord
        return x + self.map_width * y

    def index_to_coord(self, index):
        x = index % self.map_width
        y = index // self.map_width
        return x, y

    def in_map(self, coord):
        x, y = coord
        return 0 <= x < self.map_width and 0 <= y < self.map_height

    def spiral_trace_generator(self, center_index, *, layer=-1):
        x0, y0 = self.index_to_coord(center_index)
        dx = dy = 0
        if layer == -1:
            layer = max(
                x0, self.map_width - x0 - 1,
                y0, self.map_height - y0 - 1
            )
        while max(abs(dx), abs(dy)) <= layer:
            next_coord = (x0 + dx, y0 + dy)
            if self.in_map(next_coord):
                next_index = self.coord_to_index(next_coord)
                yield next_index
            if dx + dy <= 0 and dx - dy >= 0:
                dx += 1
            elif dx + dy > 0 and dx - dy <= 0:
                dx -= 1
            elif dx + dy > 0 and dx - dy > 0:
                dy += 1
            elif dx + dy <= 0 and dx - dy < 0:
                dy -= 1

    def get_surrounding_indexes_with_self(self, index, *, layer=1):
        return list(self.spiral_trace_generator(index, layer=layer))

    def get_surrounding_indexes(self, index, *, layer=1):
        result = self.get_surrounding_indexes_with_self(index, layer=layer)
        result.pop(0)
        return result

    def get_common_indexes(self, index0, index1):
        surrounding0 = self.surrounding_indexes[index0]
        surrounding1 = self.surrounding_indexes[index1]
        return self.get_union(surrounding0, surrounding1)

    def get_suburb_indexes(self, index0, index1):
        surrounding0 = self.surrounding_indexes[index0]
        surrounding1 = self.surrounding_indexes[index1]
        return self.get_difference(surrounding0, surrounding1)

    def indexes_ordered_in_spiral(self, index, index_list):
        spiral_ordered_indexes = self.spiral_trace_generator(index)
        result = []
        while index_list:
            next_index = next(spiral_ordered_indexes)
            if next_index in index_list:
                index_list.remove(next_index)
                result.append(next_index)
        return result

    @abstractmethod
    def raise_init_mine_map_error(self):
        pass

    def init_mine_indexes(self, first_index):
        safe_region_indexes = self.get_surrounding_indexes_with_self(
            first_index
        )
        map_index_choices = list(range(self.num_boxes))
        for i in safe_region_indexes:
            map_index_choices.remove(i)
        try:
            self.mine_indexes = random.sample(
                map_index_choices, self.num_mines
            )
        except ValueError:
            self.raise_init_mine_map_error()

    def init_base_map(self):
        for mine_index in self.mine_indexes:
            self.base_map[mine_index] = -1
        for mine_index in self.mine_indexes:
            for i in self.surrounding_indexes[mine_index]:
                if self.base_map[i] != -1:
                    self.base_map[i] += 1

    @abstractmethod
    def update_map(self, index):
        pass

    def reduce_num_unknown_boxes(self):
        self.num_unknown_boxes -= 1

    def reduce_num_unknown_mines(self):
        self.num_unknown_mines -= 1

    def expand_zero(self, index):
        pre_updated_zero_region = []
        zero_region = [index]
        while len(pre_updated_zero_region) != len(zero_region):
            zero_region_difference = self.get_difference(
                zero_region, pre_updated_zero_region
            )
            pre_updated_zero_region = zero_region.copy()
            for i in zero_region_difference:
                for j in self.surrounding_indexes[i]:
                    if self.base_map[j] == 0 and j not in zero_region:
                        zero_region.append(j)
        expand_region = zero_region.copy()
        for i in zero_region:
            for j in self.surrounding_indexes[i]:
                if self.view_map[j] == 9 and j not in expand_region:
                    expand_region.append(j)
        for i in self.indexes_ordered_in_spiral(index, expand_region):
            self.explore_single_safe_box(i)

    def explore_single_safe_box(self, index):
        self.reduce_num_unknown_boxes()
        self.view_map[index] = self.base_map[index]
        self.update_map(index)

    def explore_surrounding(self, index):
        indexes = self.surrounding_indexes[index]
        flags_count = [self.view_map[i] for i in indexes].count(10)
        if flags_count == self.base_map[index]:
            surrounding_mine_indexes = [
                i for i in indexes
                if self.base_map[i] == -1 and self.view_map[i] != 10
            ]
            if surrounding_mine_indexes:
                self.explode(surrounding_mine_indexes)
            else:
                for i in indexes:
                    if self.view_map[i] == 9:
                        self.explore_blank_box(i)

    def explore_blank_box(self, index):
        val = self.base_map[index]
        if val == -1:
            self.explode([index])
        elif val == 0:
            self.expand_zero(index)
        else:
            self.explore_single_safe_box(index)

    def flag_blank_box(self, index):
        self.view_map[index] = 10
        self.reduce_num_unknown_boxes()
        self.reduce_num_unknown_mines()
        self.update_map(index)

    def exploit_step(self, step):
        self.num_steps += 1
        index, step_mode = step
        if step_mode == 0 or step_mode == 3:
            if step_mode == 3:
                self.num_random_steps += 1
            self.explore_blank_box(index)
        elif step_mode == 1:
            self.explore_surrounding(index)
        elif step_mode == 2:
            self.flag_blank_box(index)
        self.check_if_win()

    def start(self, first_index):
        self.init_mine_indexes(first_index)
        self.init_base_map()
        self.game_status = 1

    def explode(self, indexes):
        indexes_generator = self.spiral_trace_generator(self.previous_index)
        for _ in range(self.num_boxes):
            i = next(indexes_generator)
            if i in indexes:
                self.view_map[i] = 11
            elif self.base_map[i] == -1 and self.view_map[i] != 10:
                self.view_map[i] = 12
            elif self.base_map[i] != -1 and self.view_map[i] == 10:
                self.view_map[i] = 13
            else:
                continue
            self.update_map(i)
        self.game_status = 3

    def win(self):
        indexes_generator = self.spiral_trace_generator(self.previous_index)
        for _ in range(self.num_boxes):
            i = next(indexes_generator)
            if self.view_map[i] == 9:
                self.flag_blank_box(i)
        self.game_status = 2

    def check_if_win(self):
        if self.game_status == 1 \
                and self.view_map.count(9) == self.num_unknown_mines:
            self.win()

    @abstractmethod
    def on_playing(self):
        pass

    def run(self):
        begin_time = time.time()
        self.on_playing()
        end_time = time.time()
        self.time_used = end_time - begin_time


class Logic(Core):
    def __init__(self, map_width, map_height, num_mines):
        Core.__init__(self, map_width, map_height, num_mines)
        self.unknown_map = [0] * self.num_boxes
        self.flags_map = [0] * self.num_boxes
        self.cached_steps = []
        self.init_unknown_map()

    def init_unknown_map(self):
        for i in range(self.num_boxes):
            self.unknown_map[i] = len(self.surrounding_indexes[i])

    def re_initialize(self):
        Core.re_initialize(self)
        self.unknown_map = [0] * self.num_boxes
        self.flags_map = [0] * self.num_boxes
        self.cached_steps = []
        self.init_unknown_map()

    def modify_surrounding_unknown_map(self, index):
        for i in self.surrounding_indexes[index]:
            self.unknown_map[i] -= 1

    def modify_surrounding_flags_map(self, index):
        for i in self.surrounding_indexes[index]:
            self.flags_map[i] += 1

    def explore_single_safe_box(self, index):
        Core.explore_single_safe_box(self, index)
        self.modify_surrounding_unknown_map(index)

    def flag_blank_box(self, index):
        Core.flag_blank_box(self, index)
        self.modify_surrounding_unknown_map(index)
        self.modify_surrounding_flags_map(index)

    def is_valuable(self, index):
        return self.unknown_map[index] != 0 and self.view_map[index] < 9

    def two_indexes_logic(self, index0, index1):
        num_common_unknown = [
            self.view_map[i] for i in self.get_common_indexes(index0, index1)
        ].count(9)
        suburb_indexes0 = self.get_suburb_indexes(index0, index1)
        suburb_indexes1 = self.get_suburb_indexes(index1, index0)
        num_unknown0 = self.unknown_map[index0] - num_common_unknown
        if self.base_map[index0] - self.base_map[index1] == num_unknown0 \
                + self.flags_map[index0] - self.flags_map[index1]:
            for i in suburb_indexes0:
                if self.view_map[i] == 9:
                    self.cached_steps.append((i, 2))
            for i in suburb_indexes1:
                if self.view_map[i] == 9:
                    self.cached_steps.append((i, 0))

    def infer_single_box(self, index):
        if not self.is_valuable(index):
            return
        if self.flags_map[index] == self.base_map[index]:
            self.cached_steps.append((index, 1))
        if self.unknown_map[index] + self.flags_map[index] \
                == self.base_map[index]:
            for i in self.surrounding_indexes[index]:
                if self.view_map[i] == 9:
                    self.cached_steps.append((i, 2))
        exp_indexes = self.sub_surrounding_indexes[index]
        for exp_index in exp_indexes:
            if self.is_valuable(exp_index):
                self.two_indexes_logic(index, exp_index)

    def make_random_choice(self):
        blank_indexes = [
            i for i in range(self.num_boxes) if self.view_map[i] == 9
        ]
        random_index = random.choice(blank_indexes)
        self.previous_index = random_index
        random_step = (random_index, 3)
        return random_step

    def make_choice(self):
        self.cached_steps = list(filter(
            lambda cached_step: self.view_map[cached_step[0]] == 9,
            self.cached_steps
        ))
        if self.cached_steps:
            return self.cached_steps.pop(0)
        inferred_box_indexes = self.spiral_trace_generator(
            self.previous_index
        )
        for _ in range(self.num_boxes):
            index = next(inferred_box_indexes)
            self.infer_single_box(index)
            if self.cached_steps:
                self.previous_index = index
                return self.cached_steps.pop(0)
        random_step = self.make_random_choice()
        return random_step

    def make_first_choice_index(self):
        first_index = self.coord_to_index(
            (self.map_width // 2, self.map_height // 2)
        )
        self.previous_index = first_index
        return first_index

    def on_playing(self):
        first_index = self.make_first_choice_index()
        self.start(first_index)
        first_step = (first_index, 0)
        self.exploit_step(first_step)
        while self.game_status == 1:
            next_step = self.make_choice()
            self.exploit_step(next_step)


class GameRecorder(object):
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

    def record(self, game_file_index, folder_path):
        json_dict = self.get_json_dict()
        file_name = str(game_file_index) + ".json"
        file_path = os.path.join(folder_path, file_name)
        assert not os.path.exists(file_path)
        with open(file_path, "w") as output_file:
            json.dump(json_dict, output_file, indent=0)


class Interface(Logic):
    BOX_CHAR_LIST = (
        ("\u3000", 0x00),  # black        "　"
        ("\uff11", 0x03),  # dark skyblue "１"
        ("\uff12", 0x0a),  # green        "２"
        ("\uff13", 0x0c),  # red          "３"
        ("\uff14", 0x05),  # dark pink    "４"
        ("\uff15", 0x04),  # dark red     "５"
        ("\uff16", 0x0b),  # skyblue      "６"
        ("\uff17", 0x07),  # dark white   "７"
        ("\uff18", 0x08),  # dark gray    "８"
        ("\u2588", 0x7f),  # white        "█"
        ("\u25cf", 0x7d),  # pink         "●"
        ("\uff0a", 0x7c),  # red          "＊"
        ("\u203b", 0x76),  # dark yellow  "※"
        ("\u2573", 0x08),  # dark gray    "╳"
        # enclosed_box: black
        # revealed_box: dark white
    )
    GAME_STATUS_LIST = (
        ("Preparing...", 0x0e),   # yellow
        ("Processing...", 0x0e),  # yellow
        ("Game won!", 0x0a),      # green
        ("Game over!", 0x0c),     # red
    )
    GAME_BASE_INFO_KEYS = ("Size", "Progress", "Mines", "Steps", "Guesses")
    CELL_SEPARATOR = "  "
    FRAME_PARTS = (
        ("\u250f", "\u2501", "\u2513"),  # ┏━┓
        ("\u2503", "\u2588", "\u2503"),  # ┃█┃
        ("\u2517", "\u2501", "\u251b"),  # ┗━┛
    )
    FINISH_MSG = "Finished!"
    INIT_FAILURE_MSG = "Fatal: Failed to form a mine map with so many mines!"
    FOLDER_NAME = "game_savings"

    def __init__(self, map_width, map_height, num_mines,
            display_mode, record_mode, sleep_per_step_if_displayed):
        """
        :param display_mode: int in range(4)
            0: Display the map and basic information after each step
            1: Display the map after each step
            2: Display basic information at the end of each game
            3: Only display the statistics data

        :param record_mode: int < 4
            0: never record
            1: always record
            2: record if won
            3: record if lost
            -n: record n best-played games
        """
        Logic.__init__(self, map_width, map_height, num_mines)
        self.display_mode = display_mode
        self.record_mode = record_mode
        self.sleep_per_step_if_displayed = sleep_per_step_if_displayed
        self.display_map = (display_mode == 0 or display_mode == 1)

        self.step_index_list = []
        self.step_mode_list = []
        self.game_file_index = -1

        self.status_info_width = 0
        self.cell_width = 0
        self.console_cols = 0
        self.console_lines = 0
        self.init_interface_params()

        self.folder_path = ""
        self.init_folder_path()

    def init_interface_params(self):
        base_info_cell_num = len(Interface.GAME_BASE_INFO_KEYS)
        longest_base_info_values = self.get_game_base_info_values_template(
            0, self.num_mines, self.num_boxes, self.num_boxes
        )
        assert base_info_cell_num == len(longest_base_info_values)
        self.status_info_width = max([
            len(val[0]) for val in Interface.GAME_STATUS_LIST
        ])
        self.cell_width = max(
            list(map(len, Interface.GAME_BASE_INFO_KEYS)) \
                + list(map(len, longest_base_info_values))
        )
        base_info_width = (self.cell_width + len(Interface.CELL_SEPARATOR)) \
            * base_info_cell_num - len(Interface.CELL_SEPARATOR)
        cols = len(COPYRIGHT_STR)
        if self.display_mode == 3:
            lines = 3
        elif self.display_mode == 2:
            cols = max(cols, base_info_width)
            lines = 6
        else:
            cols = max(cols, base_info_width, (self.map_width + 2) * 2)
            lines = self.map_height + 8
        self.console_cols = cols
        self.console_lines = lines

    def init_folder_path(self):
        main_folder = Interface.FOLDER_NAME
        if not os.path.exists(main_folder):
            os.makedirs(main_folder)
        folder_name = "-".join(map(str, (
            self.map_width, self.map_height, self.num_mines
        )))
        self.folder_path = os.path.join(main_folder, folder_name)

    def re_initialize(self):
        Logic.re_initialize(self)
        self.step_index_list = []
        self.step_mode_list = []

    def exploit_step(self, step):
        if self.record_mode != 0:
            index, step_mode = step
            self.step_index_list.append(index)
            self.step_mode_list.append(step_mode)
        Logic.exploit_step(self, step)
        if self.display_map:
            if self.display_mode == 0:
                self.print_game_base_info_values()
            if self.game_status == 1:
                time.sleep(self.sleep_per_step_if_displayed)

    def start(self, first_index):
        Logic.start(self, first_index)
        if self.display_mode == 0:
            self.print_game_status()

    def end(self):
        if self.display_mode == 3:
            return
        self.print_game_status()
        if self.display_mode != 0:
            self.print_game_base_info_values()

    def explode(self, indexes):
        Logic.explode(self, indexes)
        self.end()

    def win(self):
        Logic.win(self)
        self.end()

    def calculate_console_coord(self, index):
        x, y = self.index_to_coord(index)
        x += 1
        x *= 2
        y += 5
        return x, y

    def update_map(self, index):
        if not self.display_map:
            return
        box_char_tuple = Interface.BOX_CHAR_LIST[self.view_map[index]]
        console_coord = self.calculate_console_coord(index)
        CONSOLE.print_at(
            console_coord, box_char_tuple[0], color=box_char_tuple[1]
        )

    def print_game_status(self):
        status_tuple = Interface.GAME_STATUS_LIST[self.game_status]
        CONSOLE.print_in_line(
            1, StringTools.set_space(self.status_info_width, -1).format(
                status_tuple[0]
            ),
            color=status_tuple[1]
        )

    def get_game_base_info_values_template(self, num_unknown_boxes,
            num_unknown_mines, num_steps, num_random_steps):
        return (
            "{0} * {1}".format(self.map_width, self.map_height),
            "{0} / {1}".format(
                self.num_boxes - num_unknown_boxes, self.num_boxes
            ),
            "{0} / {1}".format(num_unknown_mines, self.num_mines),
            str(num_steps),
            str(num_random_steps),
        )

    def get_game_base_info_values(self):
        return self.get_game_base_info_values_template(
            self.num_unknown_boxes, self.num_unknown_mines,
            self.num_steps, self.num_random_steps
        )

    def print_game_base_info_keys(self):
        CONSOLE.print_list_as_table_row(
            2, Interface.GAME_BASE_INFO_KEYS, self.cell_width, 1,
            Interface.CELL_SEPARATOR
        )

    def print_game_base_info_values(self):
        game_base_info_values = self.get_game_base_info_values()
        CONSOLE.print_list_as_table_row(
            3, game_base_info_values, self.cell_width, 1,
            Interface.CELL_SEPARATOR
        )

    def init_display_frame(self):
        parts = Interface.FRAME_PARTS
        right_side_index = 2 * (self.map_width + 1)
        up_side = parts[0][0] + self.map_width * parts[0][1] + parts[0][2]
        bottom_side = parts[2][0] + self.map_width * parts[2][1] + parts[2][2]
        CONSOLE.print_in_line(4, up_side)
        for line_index in range(5, self.map_height + 5):
            CONSOLE.print_in_line(line_index, parts[1][0])
        for line_index in range(5, self.map_height + 5):
            CONSOLE.print_at((right_side_index, line_index), parts[1][2])
        CONSOLE.print_in_line(self.map_height + 5, bottom_side)

    def display_new_view_map(self):
        blank_tuple = Interface.BOX_CHAR_LIST[9]
        view_map_line_str = blank_tuple[0] * self.map_width
        for line_index in range(5, self.map_height + 5):
            CONSOLE.print_at(
                (2, line_index), view_map_line_str, color=blank_tuple[1]
            )

    def prepare_console(self, cols, lines):
        CONSOLE.clear_console()
        CONSOLE.hide_cursor()
        CONSOLE.set_console_size(cols, lines)
        CONSOLE.print_copyright_str()
        if self.display_mode != 3:
            self.print_game_base_info_keys()
            self.print_game_base_info_values()
            if self.display_map:
                self.init_display_frame()

    def get_recorder(self):
        return GameRecorder(self)

    def get_num_of_files(self):
        folder_path = self.folder_path
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        return len(os.listdir(folder_path))

    def record_game_using_recorder(self, game_recorder):
        if self.game_file_index == -1:
            self.game_file_index = self.get_num_of_files()
        else:
            self.game_file_index += 1
        game_recorder.record(self.game_file_index, self.folder_path)

    def record_game_data(self, game):
        game_recorder = game.get_recorder()
        self.record_game_using_recorder(game_recorder)

    def judge_to_record_game_data(self, game):
        if self.record_mode == 1 \
                or self.record_mode == game.game_status == 2 \
                or self.record_mode == game.game_status == 3:
            self.record_game_data(game)

    def begin_process(self):
        self.prepare_console(self.console_cols, self.console_lines)

    def run(self):
        if self.display_map:
            if self.display_mode == 0:
                self.print_game_base_info_values()
            self.display_new_view_map()
        Logic.run(self)

    @staticmethod
    def terminate_process():
        CONSOLE.print_at_end(1, Interface.FINISH_MSG, color=0x0a)
        CONSOLE.ready_to_quit()

    def raise_init_mine_map_error(self):
        CONSOLE.print_at_end(1, Interface.INIT_FAILURE_MSG, color=0x0c)
        CONSOLE.ready_to_quit()


class AutoGame(Interface):
    def run_whole_process(self):
        self.begin_process()
        self.run()
        if self.record_mode != 0:
            self.judge_to_record_game_data(self)
        self.terminate_process()


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
            self.record_game_using_recorder(game_recorder)
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
            if self.record_mode > 0:
                self.judge_to_record_game_data(game)
            elif self.record_mode < 0:
                self.update_ranking_list(game)
            game.re_initialize()
        for pair in self.ranking_list:
            game_recorder = pair[1]
            self.record_game_using_recorder(game_recorder)
        self.terminate_process()


class DisplayRecordedGame(AutoGame):
    def __init__(self, file_path, display_mode, sleep_per_step):
        with open(file_path, "r") as input_file:
            json_dict = json.load(input_file)
        AutoGame.__init__(
            self, int(json_dict["map_width"]),
            int(json_dict["map_height"]), int(json_dict["num_mines"]),
            display_mode, 0, sleep_per_step
        )
        self.mine_indexes = list(map(
            int, json_dict["mine_indexes"].split()
        ))
        self.step_index_iterator = iter(map(
            int, json_dict["step_indexes"].split()
        ))
        self.step_mode_iterator = iter(map(
            int, json_dict["step_mode_nums"]
        ))

    def init_mine_indexes(self, first_index):
        pass

    def make_choice(self):
        index = next(self.step_index_iterator)
        step_mode = next(self.step_mode_iterator)
        next_step = (index, step_mode)
        return next_step

    def make_first_choice_index(self):
        return self.make_choice()[0]


class Prompt(object):
    HINT = "\n".join([
        "Hint: When typing in parameters, you can type nothing and directly",
        "get the default value marked with '[]'."
    ])
    MODE = "Please choose a mode."
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
    MODE = (
        "Run a single game",
        "Run many times to get statistics data",
        "Display a recorded game from '{0}' file".format(Interface.FOLDER_NAME)
    )
    DISPLAY_MODE_0 = (
        "Display the map and basic information after each step",
        "Display the map after each step",
        "Only display basic information at the end of the game"
    )
    DISPLAY_MODE_1 = (
        "Display the map and basic information after each step",
        "Display the map after each step",
        "Display basic information at the end of each game",
        "Only display the statistics data"
    )
    DISPLAY_MODE_2 = (
        "Display the map and basic information after each step",
        "Display the map after each step"
    )
    RECORD_MODE_0 = (
        "No recording",
        "Always record",
        "Record if won",
        "Record if lost"
    )
    RECORD_MODE_1 = (
        "No recordings",
        "Record all games",
        "Record only won games",
        "Record only lost games",
        "Record some best-played games"
    )


class MainProcess(object):
    EXAMPLE_FILE_ID = "30-16-99-0"

    @staticmethod
    def __init__():
        CONSOLE.set_console_size_to_default()
        CONSOLE.print_copyright_str()
        process = MainProcess.input_parameters()
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

    @staticmethod
    def get_file_path(file_id):
        split_index = file_id.rfind("-")
        if split_index == -1:
            return ""
        folder_name = file_id[:split_index]
        file_name = file_id[split_index + 1:] + ".json"
        file_path = os.path.join(Interface.FOLDER_NAME, folder_name, file_name)
        try:
            open(file_path)
        except FileNotFoundError:
            return ""
        return file_path

    @staticmethod
    def handle_0():
        map_width, map_height, num_mines = MainProcess.input_specification()
        display_mode = InputTools.prompts_input(
            Prompt.DISPLAY_MODE, 0, ChoicesPrompts.DISPLAY_MODE_0
        )
        record_mode = InputTools.prompts_input(
            Prompt.RECORD_MODE, 0, ChoicesPrompts.RECORD_MODE_0
        )
        if display_mode != 2:
            sleep_per_step = MainProcess.input_sleep_per_step(0.0)
        else:
            sleep_per_step = 0.0
        return AutoGame(
            map_width, map_height, num_mines,
            display_mode, record_mode, sleep_per_step
        )

    @staticmethod
    def handle_1():
        map_width, map_height, num_mines = MainProcess.input_specification()
        num_games = InputTools.assertion_input(
            int, Prompt.NUM_GAMES, 10, lambda x: x > 0
        )
        display_mode = InputTools.prompts_input(
            Prompt.DISPLAY_MODE, 0, ChoicesPrompts.DISPLAY_MODE_1
        )
        record_mode = InputTools.prompts_input(
            Prompt.RECORD_MODE, 0, ChoicesPrompts.RECORD_MODE_1
        )
        if record_mode == 4:
            num_recorded_games = InputTools.assertion_input(
                int, Prompt.NUM_RECORDED_GAMES, 1, lambda x: 0 < x <= num_games
            )
            record_mode = -num_recorded_games
        update_freq = InputTools.assertion_input(
            int, Prompt.UPDATE_FREQ, 1, lambda x: x > 0
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

    @staticmethod
    def handle_2():
        file_id = InputTools.assertion_input(
            str, Prompt.FILE_ID, MainProcess.EXAMPLE_FILE_ID,
            MainProcess.get_file_path
        )
        file_path = MainProcess.get_file_path(file_id)
        display_mode = InputTools.prompts_input(
            Prompt.DISPLAY_MODE, 0, ChoicesPrompts.DISPLAY_MODE_2
        )
        sleep_per_step = MainProcess.input_sleep_per_step(0.0)
        return DisplayRecordedGame(
            file_path, display_mode, sleep_per_step
        )

    @staticmethod
    def input_parameters():
        CONSOLE.print_with_color(Prompt.HINT, color=0x0a)
        mode = InputTools.prompts_input(Prompt.MODE, 0, ChoicesPrompts.MODE)
        if mode == 0:
            process = MainProcess.handle_0()
        elif mode == 1:
            process = MainProcess.handle_1()
        else:
            process = MainProcess.handle_2()
        return process


if __name__ == "__main__":
    MainProcess()
