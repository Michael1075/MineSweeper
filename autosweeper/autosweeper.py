from abc import abstractmethod
import ctypes
import json
import os
import random
import sys
import time


__author__ = "Michael W"
__website__ = "https://github.com/Michael1075/autosweeper"

COPYRIGHT_STR = os.path.basename(__file__) + " - " + __website__


def f_div(a, b):
    try:
        return a / b
    except ZeroDivisionError:
        return 0.0


def average(list_obj):
    return f_div(sum(list_obj), len(list_obj))


class Core(object):
    def __init__(self, map_width, map_height, num_mines):
        self.map_width = map_width
        self.map_height = map_height
        self.num_mines = num_mines
        self.num_boxes = num_boxes = map_width * map_height
        self.mine_indexes = [0] * num_mines
        self.base_map = [0] * num_boxes
        self.view_map = [-1] * num_boxes

        self.game_status = "preparing"
        self.num_steps = 0
        self.num_random_steps = 0
        self.time_used = 0.0
        self.previous_index = 0

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
        x = y = 0
        if layer == -1:
            layer = max(
                x0, self.map_width - x0 - 1,
                y0, self.map_height - y0 - 1
            )
        while max(abs(x), abs(y)) <= layer:
            next_coord = (x0 + x, y0 + y)
            if self.in_map(next_coord):
                next_index = self.coord_to_index(next_coord)
                yield next_index
            if x + y <= 0 and x - y >= 0:
                x += 1
            elif x + y > 0 and x - y <= 0:
                x -= 1
            elif x + y > 0 and x - y > 0:
                y += 1
            elif x + y <= 0 and x - y < 0:
                y -= 1

    def get_surrounding_indexes_with_self(self, index, *, layer=1):
        return list(self.spiral_trace_generator(index, layer=layer))

    def get_surrounding_indexes(self, index, *, layer=1):
        result = self.get_surrounding_indexes_with_self(index, layer=layer)
        result.pop(0)
        return result

    def get_common_indexes(self, index0, index1):
        surrounding0 = self.get_surrounding_indexes(index0)
        surrounding1 = self.get_surrounding_indexes(index1)
        return list(set(surrounding0) & set(surrounding1))

    def indexes_ordered_in_spiral(self, index, indexes_set):
        spiral_ordered_indexes = self.spiral_trace_generator(index)
        result = []
        while indexes_set:
            next_index = next(spiral_ordered_indexes)
            if next_index in indexes_set:
                indexes_set.discard(next_index)
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
            for i in self.get_surrounding_indexes(mine_index):
                if self.base_map[i] != -1:
                    self.base_map[i] += 1

    @abstractmethod
    def update_map(self, index):
        pass

    @abstractmethod
    def modify_surrounding_unknown_map(self, index):
        pass

    @abstractmethod
    def modify_surrounding_flags_map(self, index):
        pass

    def expand_zero(self, index):
        pre_updated_zero_region = set()
        zero_region = {index}
        while len(pre_updated_zero_region) != len(zero_region):
            zero_region_difference_set = zero_region - pre_updated_zero_region
            pre_updated_zero_region = zero_region.copy()
            for i in zero_region_difference_set:
                for j in self.get_surrounding_indexes_with_self(i):
                    if self.base_map[j] == 0:
                        zero_region.add(j)
        expand_region = set()
        for i in zero_region:
            for j in self.get_surrounding_indexes_with_self(i):
                if self.view_map[j] == -1:
                    expand_region.add(j)
        for i in self.indexes_ordered_in_spiral(index, expand_region):
            self.explore_single_safe_box(i)

    def explore_single_safe_box(self, index):
        self.modify_surrounding_unknown_map(index)
        self.view_map[index] = self.base_map[index]
        self.update_map(index)

    def explore_surrounding(self, index):
        surrounding_indexes = self.get_surrounding_indexes(index)
        flags_count = [self.view_map[i] for i in surrounding_indexes].count(-2)
        if flags_count == self.base_map[index]:
            surrounding_mine_indexes = []
            for i in surrounding_indexes:
                if self.base_map[i] == -1 and self.view_map[i] != -2:
                    surrounding_mine_indexes.append(i)
            if surrounding_mine_indexes:
                self.explode(surrounding_mine_indexes)
            else:
                for i in surrounding_indexes:
                    if self.view_map[i] == -1:
                        self.explore_blank_box(i)

    def explore_blank_box(self, index):
        val = self.base_map[index]
        if val == -1:
            self.explode([index])
        elif val == 0:
            self.expand_zero(index)
        else:
            self.explore_single_safe_box(index)

    def flag_blank_box_without_updating(self, index):
        self.view_map[index] = -2
        self.modify_surrounding_unknown_map(index)
        self.modify_surrounding_flags_map(index)

    def flag_blank_box(self, index):
        self.flag_blank_box_without_updating(index)
        self.update_map(index)

    def exploit_step(self, step):
        self.num_steps += 1
        index, step_mode = step
        if step_mode in ("explore", "guess"):
            if step_mode == "guess":
                self.num_random_steps += 1
            self.explore_blank_box(index)
        elif step_mode == "explore_surrounding":
            self.explore_surrounding(index)
        elif step_mode == "flag":
            self.flag_blank_box(index)
        self.check_if_win()

    def start(self, first_index):
        self.init_mine_indexes(first_index)
        self.init_base_map()
        self.game_status = "processing"

    def explode(self, indexes):
        to_be_updates_indexes = []
        for i in indexes:
            self.view_map[i] = -3
            to_be_updates_indexes.append(i)
        for i in range(self.num_boxes):
            if self.base_map[i] == -1 and self.view_map[i] not in (-2, -3):
                self.view_map[i] = -4
                to_be_updates_indexes.append(i)
            elif self.base_map[i] != -1 and self.view_map[i] == -2:
                self.view_map[i] = -5
                to_be_updates_indexes.append(i)
        for i in self.indexes_ordered_in_spiral(
            self.previous_index, set(to_be_updates_indexes)
        ):
            self.update_map(i)
        self.game_status = "lost"

    def win(self):
        to_be_updates_indexes = []
        for i in range(self.num_boxes):
            if self.view_map[i] == -1:
                self.flag_blank_box_without_updating(i)
                to_be_updates_indexes.append(i)
        for i in self.indexes_ordered_in_spiral(
            self.previous_index, set(to_be_updates_indexes)
        ):
            self.update_map(i)
        self.game_status = "won"

    def check_if_win(self):
        if all([
            self.game_status == "processing",
            self.view_map.count(-1) == self.num_unknown_mines
        ]):
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
        num_boxes = self.num_boxes
        self.num_unknown_boxes = num_boxes
        self.num_unknown_mines = num_mines
        self.unknown_map = [0] * num_boxes
        self.flags_map = [0] * num_boxes

        self.cached_steps = []

        self.init_unknown_map()

    def init_unknown_map(self):
        for i in range(self.num_boxes):
            self.unknown_map[i] = len(self.get_surrounding_indexes(i))

    def modify_surrounding_unknown_map(self, index):
        self.num_unknown_boxes -= 1
        for i in self.get_surrounding_indexes(index):
            self.unknown_map[i] -= 1

    def modify_surrounding_flags_map(self, index):
        self.num_unknown_mines -= 1
        for i in self.get_surrounding_indexes(index):
            self.flags_map[i] += 1

    def is_valuable(self, index):
        return self.unknown_map[index] != 0 and self.view_map[index] >= 0

    def two_indexes_logic(self, index0, index1):
        num_common_unknown = [
            self.view_map[i] for i in self.get_common_indexes(index0, index1)
        ].count(-1)
        indexes0 = self.get_surrounding_indexes(index0)
        indexes1 = self.get_surrounding_indexes(index1)
        suburb_indexes0 = set(indexes0) - set(indexes1)
        suburb_indexes1 = set(indexes1) - set(indexes0)
        num_unknown0 = self.unknown_map[index0] - num_common_unknown
        if self.base_map[index0] - self.base_map[index1] == num_unknown0 \
                + self.flags_map[index0] - self.flags_map[index1]:
            for i in suburb_indexes0:
                if self.view_map[i] == -1:
                    self.cached_steps.append((i, "flag"))
            for i in suburb_indexes1:
                if self.view_map[i] == -1:
                    self.cached_steps.append((i, "explore"))

    def infer_single_box(self, index):
        if not self.is_valuable(index):
            return
        if self.flags_map[index] == self.base_map[index]:
            self.cached_steps.append((index, "explore_surrounding"))
        if self.unknown_map[index] + self.flags_map[index] \
                == self.base_map[index]:
            for i in self.get_surrounding_indexes(index):
                if self.view_map[i] == -1:
                    self.cached_steps.append((i, "flag"))
        exp_indexes = self.get_surrounding_indexes(index, layer=2)
        for exp_index in exp_indexes:
            if self.is_valuable(exp_index):
                self.two_indexes_logic(index, exp_index)

    def make_random_choice(self):
        blank_indexes = []
        for i in range(self.num_boxes):
            if self.view_map[i] == -1:
                blank_indexes.append(i)
        random_index = random.choice(blank_indexes)
        self.previous_index = random_index
        random_step = (random_index, "guess")
        return random_step

    def make_choice(self):
        self.cached_steps = list(filter(
            lambda cached_step: self.view_map[cached_step[0]] == -1,
            self.cached_steps
        ))
        if self.cached_steps:
            return self.cached_steps.pop()
        inferred_box_indexes = self.spiral_trace_generator(
            self.previous_index
        )
        for _ in range(self.num_boxes):
            index = next(inferred_box_indexes)
            self.infer_single_box(index)
            if self.cached_steps:
                self.previous_index = index
                return self.cached_steps.pop()
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
        first_step = (first_index, "explore")
        self.exploit_step(first_step)
        while self.game_status == "processing":
            next_step = self.make_choice()
            self.exploit_step(next_step)


class Interface(Logic):
    ENCLOSED_BOX_COLOR = "black"
    REVEALED_BOX_COLOR = "dark white"
    BOX_CHAR_LIST = (
        ("　", "white", ENCLOSED_BOX_COLOR),
        ("１", "dark skyblue", ENCLOSED_BOX_COLOR),
        ("２", "green", ENCLOSED_BOX_COLOR),
        ("３", "red", ENCLOSED_BOX_COLOR),
        ("４", "dark pink", ENCLOSED_BOX_COLOR),
        ("５", "dark red", ENCLOSED_BOX_COLOR),
        ("６", "skyblue", ENCLOSED_BOX_COLOR),
        ("７", "dark white", ENCLOSED_BOX_COLOR),
        ("８", "dark gray", ENCLOSED_BOX_COLOR),
        ("—", "dark gray", ENCLOSED_BOX_COLOR),
        ("※", "dark yellow", REVEALED_BOX_COLOR),
        ("※", "red", REVEALED_BOX_COLOR),
        ("●", "pink", REVEALED_BOX_COLOR),
        ("█", "white", REVEALED_BOX_COLOR),
    )
    GAME_STATUS_DICT = {
        "preparing": ("Preparing...", "yellow"),
        "processing": ("Processing...", "yellow"),
        "won": ("Game won!", "green"),
        "lost": ("Game over!", "red"),
    }
    STEP_MODE_LIST = ("explore", "explore_surrounding", "flag", "guess")
    FOLDER_NAME = "game_savings"
    CELL_SEPARATOR = "  "
    LINE_SEPARATOR_UNIT = "—"

    def __init__(self, console, map_width, map_height, num_mines, *,
            display_mode, record_mode, sleep_per_step_if_displayed):
        Logic.__init__(self, map_width, map_height, num_mines)
        self.console = console
        self.line_separator = map_width * Interface.LINE_SEPARATOR_UNIT
        self.display_mode = display_mode
        self.record_mode = record_mode
        self.sleep_per_step_if_displayed = sleep_per_step_if_displayed

        self.step_index_list = []
        self.step_mode_num_list = []

        self.status_info_width = 0
        self.cell_width = 0
        self.console_cols = 0
        self.console_lines = 0
        self.init_interface_params()

    def init_interface_params(self):
        longest_possible_base_info = self.get_game_base_info_template(
            0, self.num_mines, self.num_boxes, self.num_boxes
        )
        self.status_info_width = max([
            len(val[0]) for val in Interface.GAME_STATUS_DICT.values()
        ])
        self.cell_width = max(
            list(map(len, longest_possible_base_info.keys())) \
                + list(map(len, longest_possible_base_info.values()))
        )
        base_info_width = (self.cell_width + len(Interface.CELL_SEPARATOR)) \
            * len(longest_possible_base_info) - len(Interface.CELL_SEPARATOR)
        cols = max(len(COPYRIGHT_STR), base_info_width)
        if self.display_mode == 0:
            lines = 3
        elif self.display_mode == 1:
            lines = 6
        else:
            cols = max(cols, self.map_width * 2)
            lines = self.map_height + 8
        self.console_cols = cols
        self.console_lines = lines

    def exploit_step(self, step):
        Logic.exploit_step(self, step)
        if self.record_mode != "false":
            index, step_mode = step
            self.step_index_list.append(index)
            step_mode_num = Interface.STEP_MODE_LIST.index(step_mode)
            self.step_mode_num_list.append(step_mode_num)
        if self.display_mode in (2, 3):
            if self.display_mode == 3:
                self.print_game_base_info_values()
            if self.game_status == "processing":
                time.sleep(self.sleep_per_step_if_displayed)

    def start(self, first_index):
        Logic.start(self, first_index)
        if self.display_mode == 3:
            self.print_game_status()

    def explode(self, indexes):
        Logic.explode(self, indexes)
        if self.display_mode != 0:
            self.print_game_status()
            if self.display_mode != 3:
                self.print_game_base_info_values()

    def win(self):
        Logic.win(self)
        if self.display_mode != 0:
            self.print_game_status()
            if self.display_mode != 3:
                self.print_game_base_info_values()

    def calculate_console_coord(self, index):
        x, y = self.index_to_coord(index)
        x *= 2
        y += 5
        return x, y

    def update_map(self, index):
        if self.display_mode in (0, 1):
            return
        box_char_tuple = Interface.BOX_CHAR_LIST[self.view_map[index]]
        console_coord = self.calculate_console_coord(index)
        self.console.print_at(
            console_coord, box_char_tuple[0],
            color=box_char_tuple[1], bg_color=box_char_tuple[2],
        )

    def print_game_status(self):
        status_tuple = Interface.GAME_STATUS_DICT[self.game_status]
        string_template = "{0:<" + str(self.status_info_width) + "}"
        self.console.print_in_line(
            1, string_template.format(status_tuple[0]), color=status_tuple[1]
        )

    def get_game_base_info_template(self, num_unknown_boxes,
            num_unknown_mines, num_steps, num_random_steps):
        return {
            "Size": "{0} * {1}".format(self.map_width, self.map_height),
            "Progress": "{0} / {1}".format(
                self.num_boxes - num_unknown_boxes, self.num_boxes
            ),
            "Mines": "{0} / {1}".format(num_unknown_mines, self.num_mines),
            "Steps": str(num_steps),
            "Guesses": str(num_random_steps),
        }

    def get_game_base_info(self):
        return self.get_game_base_info_template(
            self.num_unknown_boxes, self.num_unknown_mines,
            self.num_steps, self.num_random_steps
        )

    def print_game_base_info_keys(self):
        game_base_info = self.get_game_base_info()
        self.console.print_list_as_table_row(
            2, game_base_info.keys(), self.cell_width,
            "right", Interface.CELL_SEPARATOR
        )

    def print_game_base_info_values(self):
        game_base_info = self.get_game_base_info()
        self.console.print_list_as_table_row(
            3, game_base_info.values(), self.cell_width,
            "right", Interface.CELL_SEPARATOR
        )

    def init_display_view_map(self):
        if self.display_mode == 3:
            self.print_game_base_info_values()
        self.console.print_in_line(4, self.line_separator)
        blank_tuple = Interface.BOX_CHAR_LIST[-1]
        view_map_line_str = "".join([blank_tuple[0]] * self.map_width)
        for line_index in range(5, self.map_height + 5):
            self.console.print_in_line(
                line_index, view_map_line_str,
                color=blank_tuple[1], bg_color=blank_tuple[2]
            )
        self.console.print_in_line(self.map_height + 5, self.line_separator)

    def run(self):
        if self.display_mode in (2, 3):
            self.init_display_view_map()
        Logic.run(self)
        if any([
            self.record_mode == "true",
            self.record_mode == self.game_status == "won",
            self.record_mode == self.game_status == "lost"
        ]):
            self.record_game_data()

    def generate_json_filename(self, num):
        return "-".join(map(str, (
            self.map_width, self.map_height, self.num_mines, num
        ))) + ".json"

    def get_json_dict(self):
        return {
            "map_width": str(self.map_width),
            "map_height": str(self.map_height),
            "num_mines": str(self.num_mines),
            "game_result": self.game_status,
            "progress": str(self.num_boxes - self.num_unknown_boxes),
            "num_flags": str(self.num_mines - self.num_unknown_mines),
            "num_steps": str(self.num_steps),
            "num_guesses": str(self.num_random_steps),
            "time_used": "{0:.3f}".format(self.time_used),
            "mine_indexes": " ".join(map(str, self.mine_indexes)),
            "step_indexes": " ".join(map(str, self.step_index_list)),
            "step_mode_nums": "".join(map(str, self.step_mode_num_list)),
        }

    def record_game_data(self):
        json_dict = self.get_json_dict()
        folder_name = "-".join(map(str, (
            self.map_width, self.map_height, self.num_mines
        )))
        folder_path = os.path.join(Interface.FOLDER_NAME, folder_name)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        filename = str(len(os.listdir(folder_path))) + ".json"
        file_path = os.path.join(folder_path, filename)
        with open(file_path, "w") as output_file:
            json.dump(json_dict, output_file, indent=0)

    def raise_init_mine_map_error(self):
        self.console.print_at_end(
            1, "fatal: Failed to form a mine map with so many mines!",
            color="red"
        )
        self.console.ready_to_quit()


class AutoGame(Interface):
    def run(self):
        ConsoleTools.clear_console()
        self.console.set_console_size(self.console_cols, self.console_lines)
        self.console.print_copyright_str()
        if self.display_mode != 0:
            self.print_game_base_info_keys()
        Interface.run(self)


class GameStatistics(Interface):
    KEY_VAL_SEPARATOR = " "

    def __init__(self, console, map_width, map_height, num_mines, num_games, *,
            display_mode, record_mode, update_freq,
            sleep_per_step_if_displayed, sleep_per_game_if_displayed):
        Interface.__init__(
            self, console, map_width, map_height, num_mines,
            display_mode=display_mode, record_mode=record_mode,
            sleep_per_step_if_displayed=sleep_per_step_if_displayed
        )
        self.num_games = num_games
        self.update_freq = update_freq
        self.sleep_per_game_if_displayed = sleep_per_game_if_displayed

        self.num_games_won = 0
        self.num_games_won_without_guesses = 0
        self.progress_list = []
        self.num_flags_list = []
        self.num_steps_list = []
        self.num_won_games_steps_list = []
        self.num_random_steps_list = []
        self.time_list = []
        self.won_games_time_list = []
        self.ranking_list = []
        if record_mode.startswith("some"):
            self.num_recorded_games = int(record_mode.split("-")[1])
        else:
            self.num_recorded_games = 0

        self.key_info_width = 0
        self.value_info_width = 0
        self.init_statistics_params()

    def init_statistics_params(self):
        num_games = self.num_games
        num_boxes = self.num_boxes
        num_mines = self.num_mines
        max_time = 1e4
        longest_possible_data = self.get_statistics_data_template(
            num_games, num_games, num_games, num_boxes, num_mines,
            num_boxes, num_boxes, num_boxes, max_time, max_time
        )
        statistic_info_height = len(longest_possible_data)
        self.key_info_width = max(map(len, longest_possible_data.keys()))
        self.value_info_width = max(map(len, longest_possible_data.values()))
        statistic_info_width = self.key_info_width \
            + len(GameStatistics.KEY_VAL_SEPARATOR) + self.value_info_width
        self.console_cols = max(self.console_cols, statistic_info_width)
        self.console_lines += statistic_info_height + 1

    def get_statistics_data_template(self, serial_num, num_games_won,
            num_games_won_without_guesses, avg_progress, avg_num_flags,
            avg_num_steps, avg_won_games_num_steps, avg_num_random_steps,
            avg_time, avg_won_games_time):
        return {
            "Main progress": "{0} / {1} ({2:.1%})".format(
                serial_num, self.num_games,
                f_div(serial_num, self.num_games)
            ),
            "Specification": "{0} * {1} / {2} ({3:.1%})".format(
                self.map_width, self.map_height, self.num_mines,
                f_div(self.num_mines, self.num_boxes)
            ),
            "Games won": "{0} / {1} ({2:.1%})".format(
                num_games_won, serial_num,
                f_div(num_games_won, serial_num)
            ),
            "Without guesses": "{0} / {1} ({2:.1%})".format(
                num_games_won_without_guesses, serial_num,
                f_div(num_games_won_without_guesses, serial_num)
            ),
            "Avg. progress": "{0:.3f} / {1} ({2:.1%})".format(
                avg_progress, self.num_boxes,
                f_div(avg_progress, self.num_boxes)
            ),
            "Avg. flags": "{0:.3f} / {1} ({2:.1%})".format(
                avg_num_flags, self.num_mines,
                f_div(avg_num_flags, self.num_mines)
            ),
            "Avg. steps": "{0:.3f} step(s)".format(avg_num_steps),
            "Avg. steps (won)": "{0:.3f} step(s)".format(
                avg_won_games_num_steps
            ),
            "Avg. guesses": "{0:.3f} step(s)".format(avg_num_random_steps),
            "Avg. time": "{0:.3f} ms".format(avg_time * 1e3),
            "Avg. time (won)": "{0:.3f} ms".format(
                avg_won_games_time * 1e3
            ),
        }

    def get_statistics_data(self, serial_num):
        avg_progress = average(self.progress_list)
        avg_num_flags = average(self.num_flags_list)
        avg_num_steps = average(self.num_steps_list)
        avg_won_games_num_steps = average(self.num_won_games_steps_list)
        avg_num_random_steps = average(self.num_random_steps_list)
        avg_time = average(self.time_list)
        avg_won_games_time = average(self.won_games_time_list)
        return self.get_statistics_data_template(
            serial_num, self.num_games_won,
            self.num_games_won_without_guesses, avg_progress, avg_num_flags,
            avg_num_steps, avg_won_games_num_steps,
            avg_num_random_steps, avg_time, avg_won_games_time
        )

    def print_statistics_data(self, serial_num):
        statistic_info = self.get_statistics_data(serial_num)
        if self.display_mode == 0:
            begin_line_index = 2
        elif self.display_mode == 1:
            begin_line_index = 5
        else:
            begin_line_index = self.map_height + 7
        string_template = "{0:<" + str(self.key_info_width) + "}"
        string_template += GameStatistics.KEY_VAL_SEPARATOR
        string_template += "{1:>" + str(self.value_info_width) + "}"
        for line_index, item in enumerate(statistic_info.items()):
            key, value = item
            self.console.print_in_line(
                begin_line_index + line_index,
                string_template.format(key, value)
            )

    def update_statistics_data(self, game, serial_num):
        if game.game_status == "won":
            self.num_games_won += 1
            if game.num_random_steps == 0:
                self.num_games_won_without_guesses += 1
            self.num_won_games_steps_list.append(game.num_steps)
            self.won_games_time_list.append(game.time_used)
        self.progress_list.append(
            game.num_boxes - game.num_unknown_boxes
        )
        self.num_flags_list.append(
            game.num_mines - game.num_unknown_mines
        )
        self.num_steps_list.append(game.num_steps)
        self.num_random_steps_list.append(game.num_random_steps)
        self.time_list.append(game.time_used)
        if any([
            serial_num % self.update_freq == 0,
            serial_num == self.num_games
        ]):
            self.print_statistics_data(serial_num)

    def update_ranking_list(self, game):
        if not self.num_recorded_games:
            return
        if game.num_unknown_boxes == 0:
            self.num_recorded_games -= 1
            game.record_game_data()
        elif len(self.ranking_list) < self.num_recorded_games:
            self.ranking_list.append((game.num_unknown_boxes, game))
            self.ranking_list.sort(key=lambda pair: pair[0])

    def run(self):
        ConsoleTools.clear_console()
        self.console.set_console_size(self.console_cols, self.console_lines)
        self.console.print_copyright_str()
        if self.display_mode != 0:
            self.print_game_base_info_keys()
        self.print_statistics_data(0)
        for serial_num in range(1, self.num_games + 1):
            if serial_num > 1:
                time.sleep(self.sleep_per_game_if_displayed)
            game = Interface(
                self.console, self.map_width, self.map_height, self.num_mines,
                display_mode=self.display_mode,
                record_mode=self.record_mode,
                sleep_per_step_if_displayed=self.sleep_per_step_if_displayed
            )
            game.run()
            self.update_statistics_data(game, serial_num)
            if self.ranking_list is not None:
                self.update_ranking_list(game)
        if self.ranking_list is not None:
            for pair in self.ranking_list:
                game = pair[1]
                game.record_game_data()


class DisplayRecordedGame(AutoGame):
    def __init__(self, console, file_path, *, display_mode, sleep_per_step):
        with open(file_path, "r") as input_file:
            json_dict = json.load(input_file)
        AutoGame.__init__(
            self, console, int(json_dict["map_width"]),
            int(json_dict["map_height"]), int(json_dict["num_mines"]),
            display_mode=display_mode, record_mode="false",
            sleep_per_step_if_displayed=sleep_per_step
        )
        self.mine_indexes = list(map(
            int, json_dict["mine_indexes"].split()
        ))
        self.step_index_iterator = iter(map(
            int, json_dict["step_indexes"].split()
        ))
        self.step_mode_num_iterator = iter(map(
            int, json_dict["step_mode_nums"]
        ))

    def init_mine_indexes(self, first_index):
        pass

    def make_choice(self):
        index = next(self.step_index_iterator)
        step_mode_num = next(self.step_mode_num_iterator)
        step_mode = Interface.STEP_MODE_LIST[step_mode_num]
        next_step = (index, step_mode)
        return next_step

    def make_first_choice_index(self):
        return self.make_choice()[0]


class ConsoleCursor(object):
    STD_INPUT_HANDLE = -10
    STD_OUTPUT_HANDLE = -11
    STD_ERROR_HANDLE = -12
    HANDLE_STD_OUT = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)


class ConsoleCursorInfo(ctypes.Structure, ConsoleCursor):
    _fields_ = [('dwSize', ctypes.c_int), ('bVisible', ctypes.c_int)]
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
    PALETTE = {
        "foreground colors": {
            "black": 0x00,
            "dark blue": 0x01,
            "dark green": 0x02,
            "dark skyblue": 0x03,
            "dark red": 0x04,
            "dark pink": 0x05,
            "dark yellow": 0x06,
            "dark white": 0x07,
            "dark gray": 0x08,
            "blue": 0x09,
            "green": 0x0a,
            "skyblue": 0x0b,
            "red": 0x0c,
            "pink": 0x0d,
            "yellow": 0x0e,
            "white": 0x0f,
        },
        "background colors": {
            "black": 0x00,
            "dark blue": 0x10,
            "dark green": 0x20,
            "dark skyblue": 0x30,
            "dark red": 0x40,
            "dark pink": 0x50,
            "dark yellow": 0x60,
            "dark white": 0x70,
            "dark gray": 0x80,
            "blue": 0x90,
            "green": 0xa0,
            "skyblue": 0xb0,
            "red": 0xc0,
            "pink": 0xd0,
            "yellow": 0xe0,
            "white": 0xf0,
        }
    }

    def __init__(self, fg_color_str, bg_color_str):
        if not fg_color_str:
            fg_color_str = "white"
        if not bg_color_str:
            bg_color_str = "black"
        color = self.PALETTE["foreground colors"][fg_color_str] \
            | self.PALETTE["background colors"][bg_color_str]
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
    def __show_console_window(n_cmd_show):
        ctypes.windll.user32.ShowWindow(
            ctypes.windll.kernel32.GetConsoleWindow(), n_cmd_show
        )

    @staticmethod
    def minimize_console_window():
        ConsoleTools.__show_console_window(6)

    @staticmethod
    def maximize_console_window():
        ConsoleTools.__show_console_window(3)

    @staticmethod
    def __set_cmd_text_color(*, color, bg_color=""):
        ConsoleTextColor(color, bg_color)

    @staticmethod
    def __reset_color():
        ConsoleTools.__set_cmd_text_color(color="white")

    @staticmethod
    def print_with_color(value, *, color, bg_color=""):
        ConsoleTools.__set_cmd_text_color(color=color, bg_color=bg_color)
        print(value)
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

    def print_at(self, coord, value, *, color="", bg_color=""):
        assert "\n" not in value
        assert len(value) + coord[0] <= self.__cols
        self.__move_cursor_to(coord)
        ConsoleTools.print_with_color(value, color=color, bg_color=bg_color)

    def print_in_line(self, line_index, value, *, color="", bg_color=""):
        self.print_at((0, line_index), value, color=color, bg_color=bg_color)

    def print_list_as_table_row(self, line_index, list_obj,
            cell_width, align, cell_separator):
        alignment_dict = {"left": "<", "center": "^", "right": ">"}
        string_template_list = [
            "{" + str(k) + ":" + alignment_dict[align] + str(cell_width) + "}"
            for k in range(len(list_obj))
        ]
        self.print_in_line(
            line_index,
            cell_separator.join(string_template_list).format(*list_obj)
        )

    def print_copyright_str(self):
        self.print_in_line(0, COPYRIGHT_STR)

    def print_at_end(self, reversed_line_index, val, *, color="", bg_color=""):
        line_index = self.__lines - reversed_line_index - 1
        self.print_in_line(
            line_index, val, color=color, bg_color=bg_color
        )

    def ready_to_quit(self):
        self.print_at_end(0, "Press any key to quit...")
        ConsoleTools.show_cursor()
        os.system(" ".join(["pause", ">", os.devnull]))
        ConsoleTools.clear_console()
        self.set_console_size_to_default()
        sys.exit()


class InputTools(object):
    @staticmethod
    def input_with_default_val(prompt, default_val):
        val = input(prompt)
        if not val:
            val = default_val
        return val

    @staticmethod
    def input_again(default_val):
        ConsoleTools.print_with_color("Wrong input!", color="red")
        return InputTools.input_with_default_val(
            "Please input again: ", default_val
        )

    @staticmethod
    def check_input(val, data_cls, assert_func):
        try:
            result = data_cls(val)
        except ValueError:
            return False
        if assert_func is not None and not assert_func(result):
            return False
        return True

    @staticmethod
    def input_loop(base_prompt, prompt, data_cls, default_val, assert_func):
        print(base_prompt)
        val = InputTools.input_with_default_val(prompt, default_val)
        while not InputTools.check_input(val, data_cls, assert_func):
            val = InputTools.input_again(default_val)
        return data_cls(val)

    @staticmethod
    def free_input(base_prompt, data_cls, default_val):
        assert_func = lambda x: True
        return InputTools.assertion_input(
            base_prompt, data_cls, default_val, assert_func
        )

    @staticmethod
    def assertion_input(base_prompt, data_cls, default_val, assert_func):
        suffix = "[{0}]: ".format(default_val)
        return InputTools.input_loop(
            base_prompt, suffix, data_cls, default_val, assert_func
        )

    @staticmethod
    def choices_input(base_prompt, data_cls, default_val, choices):
        assert_func = lambda x: x in choices
        choices_copy = choices.copy()
        choices_copy[choices.index(default_val)] = "[{0}]".format(default_val)
        suffix = "/".join(map(str, choices_copy))
        suffix = "({0}): ".format(suffix)
        return InputTools.input_loop(
            base_prompt, suffix, data_cls, default_val, assert_func
        )

    @staticmethod
    def prompts_input(base_prompt, data_cls, default_val, choices_prompts):
        choices = list(range(len(choices_prompts)))
        longest_index_num = len(choices_prompts) - 1
        index_num_template = " - {0:" \
            + str(len(str(longest_index_num))) + "}. "
        longest_index_num_str = index_num_template.format(
            longest_index_num
        )
        for choice_num, choices_prompt in enumerate(choices_prompts):
            prompt_tail = "." if choice_num == longest_index_num else ";"
            choices_prompts[choice_num] = index_num_template.format(
                choice_num
            ) + choices_prompt.replace(
                "\n", "\n" + len(longest_index_num_str) * " "
            ) + prompt_tail
        base_prompt = "\n".join([base_prompt] + choices_prompts)
        return InputTools.choices_input(
            base_prompt, data_cls, default_val, choices
        )


class Main(object):
    def __init__(self):
        self.console = ConsoleTools()
        self.console.maximize_console_window()
        self.console.set_console_size_to_default()
        self.console.print_copyright_str()
        self.input_parameters()
        self.console.print_at_end(1, "Finished!", color="green")
        self.console.ready_to_quit()

    @staticmethod
    def input_specification():
        map_width = InputTools.assertion_input(
            "Please input the width of the map.",
            int, 30, lambda x: x > 0
        )
        map_height = InputTools.assertion_input(
            "Please input the height of the map.",
            int, 16, lambda x: x > 0
        )
        num_mines = InputTools.assertion_input(
            "Please input the number of mines.",
            int, 99, lambda x: x > 0
        )
        return map_width, map_height, num_mines

    @staticmethod
    def input_sleep_per_step(default_time):
        sleep_per_step = InputTools.assertion_input(
            "How long shall the computer sleep after each step?",
            float, default_time, lambda x: x >= 0.0
        )
        return sleep_per_step

    @staticmethod
    def input_sleep_per_game(default_time):
        sleep_per_step = InputTools.assertion_input(
            "How long shall the computer sleep after each game?",
            float, default_time, lambda x: x >= 0.0
        )
        return sleep_per_step

    @staticmethod
    def get_file_path(file_id):
        split_index = file_id.rfind("-")
        if split_index == -1:
            return ""
        folder_name = file_id[:split_index]
        filename = file_id[split_index + 1:] + ".json"
        file_path = os.path.join(
            Interface.FOLDER_NAME, folder_name, filename
        )
        try:
            open(file_path)
        except FileNotFoundError:
            return ""
        return file_path

    def handle_0(self):
        map_width, map_height, num_mines = Main.input_specification()
        display_mode = InputTools.prompts_input(
            "Please choose a display mode.",
            int, 2, [
                "Only display some basic information at the end of the game",
                "Display the map updating after each step",
                "Display the map and some basic information updating after "
                "each step"
            ]
        ) + 1
        record_mode_int = InputTools.prompts_input(
            "Please choose a recording mode to determine whether a game will"
            "be recorded.",
            int, 0, [
                "No recording",
                "Record if won",
                "Record if lost",
                "Always record"
            ]
        )
        record_mode_choices = ["false", "won", "lost", "true"]
        record_mode = record_mode_choices[record_mode_int]
        if display_mode:
            sleep_per_step = Main.input_sleep_per_step(0.0)
        else:
            sleep_per_step = 0.0
        ConsoleTools.hide_cursor()
        process_0 = AutoGame(
            self.console, map_width, map_height, num_mines,
            display_mode=display_mode, record_mode=record_mode,
            sleep_per_step_if_displayed=sleep_per_step
        )
        process_0.run()

    def handle_1(self):
        map_width, map_height, num_mines = Main.input_specification()
        num_games = InputTools.assertion_input(
            "Please input times that the game should be played for.",
            int, 10, lambda x: x > 0
        )
        display_mode = InputTools.prompts_input(
            "Please choose a display mode.",
            int, 3, [
                "Only display the statistics data",
                "Display some basic information at the end of each game",
                "Display the map updating after each step",
                "Display the map and some basic information updating after "
                "each step"
            ]
        )
        record_mode_int = InputTools.prompts_input(
            "Please choose a recording mode to determine whether a game will"
            "be recorded.",
            int, 0, [
                "No recordings",
                "Record only won games",
                "Record only lost games",
                "Record all games",
                "Record some best-playing games"
            ]
        )
        record_mode_choices = ["false", "won", "lost", "true", "some"]
        record_mode = record_mode_choices[record_mode_int]
        if record_mode == "some":
            num_recorded_games = InputTools.assertion_input(
                "How many games shall be recorded (1 at least)?",
                int, 1, lambda x: 0 < x <= num_games
            )
            record_mode = "some-" + str(num_recorded_games)
        update_freq = InputTools.assertion_input(
            "After how many games should the statistics data be refreshed?",
            int, 1, lambda x: x > 0
        )
        if display_mode:
            sleep_per_step = Main.input_sleep_per_step(0.0)
            sleep_per_game = Main.input_sleep_per_game(0.0)
        else:
            sleep_per_step = 0.0
            sleep_per_game = 0.0
        ConsoleTools.hide_cursor()
        process_1 = GameStatistics(
            self.console, map_width, map_height, num_mines, num_games,
            display_mode=display_mode, record_mode=record_mode,
            update_freq=update_freq,
            sleep_per_step_if_displayed=sleep_per_step,
            sleep_per_game_if_displayed=sleep_per_game
        )
        process_1.run()

    def handle_2(self):
        file_id = InputTools.assertion_input(
            "Please input the file-id of the game to be displayed.",
            str, "30-16-99-0", Main.get_file_path
        )
        file_path = Main.get_file_path(file_id)
        display_mode = InputTools.prompts_input(
            "Please choose a display mode.",
            int, 1, [
                "Display the map updating after each step",
                "Display the map and some basic information updating after "
                "each step"
            ]
        ) + 2
        sleep_per_step = Main.input_sleep_per_step(0.0)
        ConsoleTools.hide_cursor()
        process_2 = DisplayRecordedGame(
            self.console, file_path,
            display_mode=display_mode, sleep_per_step=sleep_per_step
        )
        process_2.run()

    def input_parameters(self):
        ConsoleTools.print_with_color(
            "Hint: When inputting parameters, you can type nothing and "
            "directly get the\n"
            "default value marked with '[]'.",
            color="green"
        )
        mode = InputTools.prompts_input("Please choose a mode.",
            int, 0, [
                "Run a single game",
                "Run many times to get statistics data",
                "Display a recorded game from '{0}' file".format(
                    Interface.FOLDER_NAME
                )
            ]
        )
        if mode == 0:
            self.handle_0()
        elif mode == 1:
            self.handle_1()
        elif mode == 2:
            self.handle_2()


if __name__ == "__main__":
    Main()
