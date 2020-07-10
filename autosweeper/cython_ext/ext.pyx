# distutils: language=c++

#from libcpp.pair cimport pair
#from libcpp.vector cimport vector

from cpp_ext cimport ConsoleTools
from cpp_ext cimport Interface


cdef class PyInterface:
    cdef Interface *thisptr

    def __cinit__(self, int map_width, int map_height, int num_mines,
            int display_mode, int record_mode, float sleep_per_step_if_displayed):
        self.thisptr = new Interface(map_width, map_height, num_mines,
            display_mode, record_mode, sleep_per_step_if_displayed)

    def __dealloc__(self):
        del self.thisptr

    property map_width:
        def __get__(self):
            return self.thisptr.map_width

    property map_height:
        def __get__(self):
            return self.thisptr.map_height

    property num_mines:
        def __get__(self):
            return self.thisptr.num_mines

    property num_boxes:
        def __get__(self):
            return self.thisptr.num_boxes

    property num_unknown_boxes:
        def __get__(self):
            return self.thisptr.num_unknown_boxes

    property num_unknown_mines:
        def __get__(self):
            return self.thisptr.num_unknown_mines

    property mine_indexes:
        def __get__(self):
            return self.thisptr.mine_indexes

    property game_status:
        def __get__(self):
            return self.thisptr.game_status

    property num_steps:
        def __get__(self):
            return self.thisptr.num_steps

    property num_random_steps:
        def __get__(self):
            return self.thisptr.num_random_steps

    property time_used:
        def __get__(self):
            return self.thisptr.time_used

    property display_mode:
        def __get__(self):
            return self.thisptr.display_mode

    property record_mode:
        def __get__(self):
            return self.thisptr.record_mode

    property sleep_per_step_if_displayed:
        def __get__(self):
            return self.thisptr.sleep_per_step_if_displayed

    property step_index_list:
        def __get__(self):
            return self.thisptr.step_index_list

    property step_mode_list:
        def __get__(self):
            return self.thisptr.step_mode_list

    property console_cols:
        def __get__(self):
            return self.thisptr.console_cols

    property console_lines:
        def __get__(self):
            return self.thisptr.console_lines

    def re_initialize(self):
        self.thisptr.re_initialize()

    def prepare_console(self, int cols, int lines):
        self.thisptr.prepare_console(cols, lines)

    def run(self):
        self.thisptr.run()

    def terminate_process(self):
        self.thisptr.terminate_process()


cdef class PyConsoleTools:
    cdef ConsoleTools *thisptr

    def __cinit__(self):
        self.thisptr = new ConsoleTools()

    def __dealloc__(self):
        del self.thisptr

    def print_with_color(self, str value, int color=0x0f):
        self.thisptr.print_with_color(value.encode(), color)

    def set_console_size_to_default(self):
        self.thisptr.set_console_size_to_default()

    def print_at(self, tuple coord, str value, int color=0x0f):
        self.thisptr.print_at(coord, value.encode(), color)

    def print_in_line(self, int line_index, str value, int color=0x0f):
        self.thisptr.print_in_line(line_index, value.encode(), color)

    def print_copyright_str(self):
        self.thisptr.print_copyright_str()
