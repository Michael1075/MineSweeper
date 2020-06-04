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
        self.mine_indexes = [-1] * num_mines
        self.base_map = [0] * num_boxes
        self.view_map = [9] * num_boxes

        self.game_status = 0
        self.num_steps = 0
        self.num_random_steps = 0
        self.previous_index = 0
        self.time_used = 0.0

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
        return [e for e in surrounding0 if e in surrounding1]

    def get_suburb_indexes(self, index0, index1):
        surrounding0 = self.get_surrounding_indexes(index0)
        surrounding1 = self.get_surrounding_indexes(index1)
        return [e for e in surrounding0 if e not in surrounding1]

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
        pre_updated_zero_region = []
        zero_region = [index]
        while len(pre_updated_zero_region) != len(zero_region):
            zero_region_difference = [
                e for e in zero_region if e not in pre_updated_zero_region
            ]
            pre_updated_zero_region = zero_region.copy()
            for i in zero_region_difference:
                for j in self.get_surrounding_indexes_with_self(i):
                    if self.base_map[j] == 0 and j not in zero_region:
                        zero_region.append(j)
        expand_region = []
        for i in zero_region:
            for j in self.get_surrounding_indexes_with_self(i):
                if self.view_map[j] == 9 and j not in expand_region:
                    expand_region.append(j)
        for i in self.indexes_ordered_in_spiral(index, expand_region):
            self.explore_single_safe_box(i)

    def explore_single_safe_box(self, index):
        self.modify_surrounding_unknown_map(index)
        self.view_map[index] = self.base_map[index]
        self.update_map(index)

    def explore_surrounding(self, index):
        surrounding_indexes = self.get_surrounding_indexes(index)
        flags_count = [self.view_map[i] for i in surrounding_indexes].count(10)
        if flags_count == self.base_map[index]:
            surrounding_mine_indexes = []
            for i in surrounding_indexes:
                if self.base_map[i] == -1 and self.view_map[i] != 10:
                    surrounding_mine_indexes.append(i)
            if surrounding_mine_indexes:
                self.explode(surrounding_mine_indexes)
            else:
                for i in surrounding_indexes:
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

    def flag_blank_box_without_updating(self, index):
        self.view_map[index] = 10
        self.modify_surrounding_unknown_map(index)
        self.modify_surrounding_flags_map(index)

    def flag_blank_box(self, index):
        self.flag_blank_box_without_updating(index)
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
        to_be_updates_indexes = []
        for i in indexes:
            self.view_map[i] = 11
            to_be_updates_indexes.append(i)
        for i in range(self.num_boxes):
            if self.base_map[i] == -1 and self.view_map[i] != 10 \
                    and self.view_map[i] != 11:
                self.view_map[i] = 12
                to_be_updates_indexes.append(i)
            elif self.base_map[i] != -1 and self.view_map[i] == 10:
                self.view_map[i] = 13
                to_be_updates_indexes.append(i)
        for i in self.indexes_ordered_in_spiral(
            self.previous_index, to_be_updates_indexes
        ):
            self.update_map(i)
        self.game_status = 3

    def win(self):
        to_be_updates_indexes = []
        for i in range(self.num_boxes):
            if self.view_map[i] == 9:
                self.flag_blank_box_without_updating(i)
                to_be_updates_indexes.append(i)
        for i in self.indexes_ordered_in_spiral(
            self.previous_index, to_be_updates_indexes
        ):
            self.update_map(i)
        self.game_status = 2

    @abstractmethod
    def check_if_win(self):
        pass

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
            for i in self.get_surrounding_indexes(index):
                if self.view_map[i] == 9:
                    self.cached_steps.append((i, 2))
        exp_indexes = self.get_surrounding_indexes(index, layer=2)
        for exp_index in exp_indexes:
            if self.is_valuable(exp_index):
                self.two_indexes_logic(index, exp_index)

    def make_random_choice(self):
        blank_indexes = []
        for i in range(self.num_boxes):
            if self.view_map[i] == 9:
                blank_indexes.append(i)
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
                return self.cached_steps.pop()
        random_step = self.make_random_choice()
        return random_step

    def make_first_choice_index(self):
        first_index = self.coord_to_index(
            (self.map_width // 2, self.map_height // 2)
        )
        self.previous_index = first_index
        return first_index

    def check_if_win(self):
        if self.game_status == 1 \
                and self.view_map.count(9) == self.num_unknown_mines:
            self.win()

    def on_playing(self):
        first_index = self.make_first_choice_index()
        self.start(first_index)
        first_step = (first_index, 0)
        self.exploit_step(first_step)
        while self.game_status == 1:
            next_step = self.make_choice()
            self.exploit_step(next_step)


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
        return {
            "map_width": str(self.map_width),
            "map_height": str(self.map_height),
            "num_mines": str(self.num_mines),
            "game_result": "won" if self.game_status == 2 else "lost",
            "progress": str(self.progress),
            "num_flags": str(self.num_flags),
            "num_steps": str(self.num_steps),
            "num_guesses": str(self.num_guesses),
            "time_used": "{0:.3f}".format(self.time_used),
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
    LINE_SEPARATOR_UNIT = "\u2014"  # "—"
    GAME_STATUS_LIST = (
        ("Preparing...", 0x0e),   # yellow
        ("Processing...", 0x0e),  # yellow
        ("Game won!", 0x0a),      # green
        ("Game over!", 0x0c),     # red
    )
    GAME_BASE_INFO_KEYS = ("Size", "Progress", "Mines", "Steps", "Guesses")
    CELL_SEPARATOR = "  "

    def __init__(self, console, map_width, map_height, num_mines,
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
        self.console = console
        self.line_separator = map_width * Interface.LINE_SEPARATOR_UNIT
        self.display_mode = display_mode
        self.record_mode = record_mode
        self.sleep_per_step_if_displayed = sleep_per_step_if_displayed

        self.step_index_list = []
        self.step_mode_list = []

        self.status_info_width = 0
        self.cell_width = 0
        self.console_cols = 0
        self.console_lines = 0
        self.init_interface_params()

    def init_interface_params(self):
        longest_base_info_values = self.get_game_base_info_values_template(
            0, self.num_mines, self.num_boxes, self.num_boxes
        )
        self.status_info_width = max([
            len(val[0]) for val in Interface.GAME_STATUS_LIST
        ])
        self.cell_width = max(
            list(map(len, Interface.GAME_BASE_INFO_KEYS)) \
                + list(map(len, longest_base_info_values))
        )
        base_info_width = (self.cell_width + len(Interface.CELL_SEPARATOR)) \
            * len(Interface.GAME_BASE_INFO_KEYS) - len(Interface.CELL_SEPARATOR)
        cols = max(len(COPYRIGHT_STR), base_info_width)
        if self.display_mode == 3:
            lines = 3
        elif self.display_mode == 2:
            lines = 6
        else:
            cols = max(cols, self.map_width * 2)
            lines = self.map_height + 8
        self.console_cols = cols
        self.console_lines = lines

    def re_initialize(self):
        num_boxes = self.num_boxes
        num_mines = self.num_mines

        self.mine_indexes = [-1] * num_mines
        self.base_map = [0] * num_boxes
        self.view_map = [9] * num_boxes
        self.unknown_map = [0] * num_boxes
        self.flags_map = [0] * num_boxes

        self.game_status = 0
        self.num_steps = 0
        self.num_random_steps = 0
        self.previous_index = 0
        self.time_used = 0.0

        self.num_unknown_boxes = num_boxes
        self.num_unknown_mines = num_mines

        self.cached_steps = []
        self.step_index_list = []
        self.step_mode_list = []

        self.init_unknown_map()

    def exploit_step(self, step):
        if self.record_mode != 0:
            index, step_mode = step
            self.step_index_list.append(index)
            self.step_mode_list.append(step_mode)
        Logic.exploit_step(self, step)
        if self.display_mode == 0 or self.display_mode == 1:
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
        x *= 2
        y += 5
        return x, y

    def update_map(self, index):
        if self.display_mode == 2 or self.display_mode == 3:
            return
        box_char_tuple = Interface.BOX_CHAR_LIST[self.view_map[index]]
        console_coord = self.calculate_console_coord(index)
        self.console.print_at(
            console_coord, box_char_tuple[0], color=box_char_tuple[1]
        )

    def print_game_status(self):
        status_tuple = Interface.GAME_STATUS_LIST[self.game_status]
        string_template = "{0:<" + str(self.status_info_width) + "}"
        self.console.print_in_line(
            1, string_template.format(status_tuple[0]), color=status_tuple[1]
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
        self.console.print_list_as_table_row(
            2, Interface.GAME_BASE_INFO_KEYS, self.cell_width, 1,
            Interface.CELL_SEPARATOR
        )

    def print_game_base_info_values(self):
        game_base_info_values = self.get_game_base_info_values()
        self.console.print_list_as_table_row(
            3, game_base_info_values, self.cell_width, 1,
            Interface.CELL_SEPARATOR
        )

    def init_display_frame(self):
        self.console.print_in_line(4, self.line_separator)
        self.console.print_in_line(self.map_height + 5, self.line_separator)
        # TODO: a rectangle frame

    def display_new_view_map(self):
        blank_tuple = Interface.BOX_CHAR_LIST[9]
        view_map_line_str = blank_tuple[0] * self.map_width
        for line_index in range(5, self.map_height + 5):
            self.console.print_in_line(
                line_index, view_map_line_str, color=blank_tuple[1]
            )

    def run(self):
        if self.display_mode == 0 or self.display_mode == 1:
            if self.display_mode == 0:
                self.print_game_base_info_values()
            self.display_new_view_map()
        Logic.run(self)
        if self.record_mode == 1 \
                or self.record_mode == self.game_status == 2 \
                or self.record_mode == self.game_status == 3:
            self.record_game_data()

    def get_recorder(self):
        return GameRecorder(self)

    def record_game_data(self):
        recorder = self.get_recorder()
        recorder.record()

    def raise_init_mine_map_error(self):
        self.console.print_at_end(
            1, "fatal: Failed to form a mine map with so many mines!",
            color=0x0c
        )
        self.console.ready_to_quit()


class AutoGame(Interface):
    def run(self):
        ConsoleTools.clear_console()
        self.console.set_console_size(self.console_cols, self.console_lines)
        self.console.print_copyright_str()
        if self.display_mode != 3:
            self.print_game_base_info_keys()
            if self.display_mode == 0 or self.display_mode == 1:
                self.init_display_frame()
        Interface.run(self)


class GameStatistics(Interface):
    STATISTICS_KEYS = (
        "Main progress", "Specification", "Games won", "Without guesses",
        "Avg. progress", "Avg. flags", "Avg. steps", "Avg. steps (won)",
        "Avg. guesses", "Avg. time", "Avg. time (won)"
    )
    KEY_VAL_SEPARATOR = " "

    def __init__(self, console, map_width, map_height, num_mines, num_games,
            display_mode, record_mode, update_freq,
            sleep_per_step_if_displayed, sleep_per_game_if_displayed):
        Interface.__init__(
            self, console, map_width, map_height, num_mines,
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
        self.ranking_list = [(self.num_boxes, None)] * self.num_recorded_games

        self.key_info_width = 0
        self.value_info_width = 0
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
        self.key_info_width = max(map(len, GameStatistics.STATISTICS_KEYS))
        self.value_info_width = max(map(len, longest_statistics_values))
        statistic_info_width = self.key_info_width \
            + len(GameStatistics.KEY_VAL_SEPARATOR) + self.value_info_width
        self.console_cols = max(self.console_cols, statistic_info_width)
        self.console_lines += statistic_info_height + 1

    def get_statistics_values_template(self, serial_num, num_games_won,
            num_games_won_without_guesses, avg_progress, avg_num_flags,
            avg_num_steps, avg_won_games_num_steps, avg_num_random_steps,
            avg_time, avg_won_games_time):
        return (
            "{0} / {1} ({2:.1%})".format(
                serial_num, self.num_games,
                f_div(serial_num, self.num_games)
            ),
            "{0} * {1} / {2} ({3:.1%})".format(
                self.map_width, self.map_height, self.num_mines,
                f_div(self.num_mines, self.num_boxes)
            ),
            "{0} / {1} ({2:.1%})".format(
                num_games_won, serial_num,
                f_div(num_games_won, serial_num)
            ),
            "{0} / {1} ({2:.1%})".format(
                num_games_won_without_guesses, serial_num,
                f_div(num_games_won_without_guesses, serial_num)
            ),
            "{0:.3f} / {1} ({2:.1%})".format(
                avg_progress, self.num_boxes,
                f_div(avg_progress, self.num_boxes)
            ),
            "{0:.3f} / {1} ({2:.1%})".format(
                avg_num_flags, self.num_mines,
                f_div(avg_num_flags, self.num_mines)
            ),
            "{0:.3f} step(s)".format(avg_num_steps),
            "{0:.3f} step(s)".format(
                avg_won_games_num_steps
            ),
            "{0:.3f} step(s)".format(avg_num_random_steps),
            "{0:.3f} ms".format(avg_time * 1e3),
            "{0:.3f} ms".format(
                avg_won_games_time * 1e3
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
        string_template = "{0:<" + str(self.key_info_width) + "}"
        string_template += GameStatistics.KEY_VAL_SEPARATOR
        for line_index, statistics_key in enumerate(
            GameStatistics.STATISTICS_KEYS
        ):
            self.console.print_in_line(
                begin_line_index + line_index,
                string_template.format(statistics_key)
            )

    def print_statistics_values(self, serial_num):
        statistics_values = self.get_statistics_values(serial_num)
        begin_line_index = self.get_statistics_begin_line_index()
        begin_col_index = self.key_info_width \
            + len(GameStatistics.KEY_VAL_SEPARATOR)
        string_template = "{0:>" + str(self.value_info_width) + "}"
        for line_index, statistics_val in enumerate(statistics_values):
            self.console.print_at(
                (begin_col_index, begin_line_index + line_index),
                string_template.format(statistics_val)
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
        list_length = self.num_recorded_games
        if not list_length:
            return
        num_unknown_boxes = game.num_unknown_boxes
        insertion_index = list_length - 1
        while insertion_index > -1 \
                and num_unknown_boxes < self.ranking_list[insertion_index][0]:
            insertion_index -= 1
        insertion_index += 1
        if insertion_index < list_length:
            for i in range(list_length - 1, insertion_index, -1):
                self.ranking_list[i] = self.ranking_list[i - 1]
            game_recorder = game.get_recorder()
            self.ranking_list[insertion_index] = (
                num_unknown_boxes, game_recorder
            )
            if num_unknown_boxes == 0:
                game_recorder.record()

    def run(self):
        ConsoleTools.clear_console()
        self.console.set_console_size(self.console_cols, self.console_lines)
        self.console.print_copyright_str()
        if self.display_mode != 3:
            self.print_game_base_info_keys()
            if self.display_mode == 0 or self.display_mode == 1:
                self.init_display_frame()
        self.print_statistics_keys()
        self.print_statistics_values(0)
        game = Interface(
            self.console, self.map_width, self.map_height, self.num_mines,
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
        for pair in self.ranking_list[self.num_games_won:]:
            game_recorder = pair[1]
            game_recorder.record()


class DisplayRecordedGame(AutoGame):
    def __init__(self, console, file_path, display_mode, sleep_per_step):
        with open(file_path, "r") as input_file:
            json_dict = json.load(input_file)
        AutoGame.__init__(
            self, console, int(json_dict["map_width"]),
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
            3: dark skyblue
            4: dark red
            5: dark pink
            6: dark yellow
            7: dark white
            8: dark gray
            9: blue
            a: green
            b: skyblue
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
    def __set_cmd_text_color(color):
        ConsoleTextColor(color)

    @staticmethod
    def __reset_color():
        ConsoleTools.__set_cmd_text_color(0x0f)

    @staticmethod
    def print_with_color(value, *, color):
        ConsoleTools.__set_cmd_text_color(color)
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

    def print_at(self, coord, value, *, color=0x0f):
        assert "\n" not in value
        assert len(value) + coord[0] <= self.__cols
        self.__move_cursor_to(coord)
        ConsoleTools.print_with_color(value, color=color)

    def print_in_line(self, line_index, value, *, color=0x0f):
        self.print_at((0, line_index), value, color=color)

    def print_list_as_table_row(self, line_index, list_obj,
            cell_width, align, cell_separator):
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
        string_template_list = [
            "{" + str(k) + ":" + align_mark + str(cell_width) + "}"
            for k in range(len(list_obj))
        ]
        self.print_in_line(
            line_index,
            cell_separator.join(string_template_list).format(*list_obj)
        )

    def print_copyright_str(self):
        self.print_in_line(0, COPYRIGHT_STR)

    def print_at_end(self, reversed_line_index, val, *, color=0x0f):
        line_index = self.__lines - reversed_line_index - 1
        self.print_in_line(line_index, val, color=color)

    def ready_to_quit(self):
        self.print_at_end(0, "Press any key to quit...")
        ConsoleTools.show_cursor()
        os.system(" ".join(("pause", ">", os.devnull)))
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
        ConsoleTools.print_with_color("Wrong input!", color=0x0c)
        return InputTools.input_with_default_val(
            "Please input again: ", default_val
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
        index_num_template = " - {0:" + str(len(str(longest_index_num))) + "}. "
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
    MODE = "Please choose a mode."
    MAP_WIDTH = "Please input the width of the map."
    MAP_HEIGHT = "Please input the height of the map."
    NUM_MINES = "Please input the number of mines."
    NUM_GAMES = "Please input times that the game should be played for."
    FILE_ID = "Please input the file-id of the game to be displayed."
    DISPLAY_MODE = "\n".join([
        "Please choose a display mode to determine how each game will be",
        "displayed (1 is recommended if the board is too large)."
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
        "Display a recorded game from '{0}' file".format(
            GameRecorder.FOLDER_NAME
        )
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
    def __init__(self):
        self.console = ConsoleTools()
        self.console.maximize_console_window()
        self.console.set_console_size_to_default()
        self.console.print_copyright_str()
        self.input_parameters()
        self.console.print_at_end(1, "Finished!", color=0x0a)
        self.console.ready_to_quit()

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
        filename = file_id[split_index + 1:] + ".json"
        file_path = os.path.join(
            GameRecorder.FOLDER_NAME, folder_name, filename
        )
        try:
            open(file_path)
        except FileNotFoundError:
            return ""
        return file_path

    def handle_0(self):
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
        ConsoleTools.hide_cursor()
        process_0 = AutoGame(
            self.console, map_width, map_height, num_mines,
            display_mode, record_mode, sleep_per_step
        )
        process_0.run()

    def handle_1(self):
        map_width, map_height, num_mines = MainProcess.input_specification()
        num_games = InputTools.assertion_input(
            int, Prompt.NUM_GAMES, 10, lambda x: x > 0
        )
        display_mode = InputTools.prompts_input(
            Prompt.DISPLAY_MODE, 0, ChoicesPrompts.DISPLAY_MODE_0
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
        ConsoleTools.hide_cursor()
        process_1 = GameStatistics(
            self.console, map_width, map_height, num_mines, num_games,
            display_mode, record_mode, update_freq,
            sleep_per_step, sleep_per_game
        )
        process_1.run()

    def handle_2(self):
        file_id = InputTools.assertion_input(
            str, Prompt.FILE_ID, "30-16-99-0", MainProcess.get_file_path
        )
        file_path = MainProcess.get_file_path(file_id)
        display_mode = InputTools.prompts_input(
            Prompt.DISPLAY_MODE, 0, ChoicesPrompts.DISPLAY_MODE_2
        )
        sleep_per_step = MainProcess.input_sleep_per_step(0.0)
        ConsoleTools.hide_cursor()
        process_2 = DisplayRecordedGame(
            self.console, file_path, display_mode, sleep_per_step
        )
        process_2.run()

    def input_parameters(self):
        ConsoleTools.print_with_color(Prompt.HINT, color=0x0a)
        mode = InputTools.prompts_input(Prompt.MODE, 0, ChoicesPrompts.MODE)
        if mode == 0:
            self.handle_0()
        elif mode == 1:
            self.handle_1()
        elif mode == 2:
            self.handle_2()


if __name__ == "__main__":
    MainProcess()
