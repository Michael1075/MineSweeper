# distutils: language=c++

from libcpp.pair cimport pair
from libcpp.string cimport string
from libcpp.vector cimport vector


cdef extern from "cpp_ext.cpp":
    cdef cppclass Interface:
        int map_width
        int map_height
        int num_mines
        int num_boxes
        int num_unknown_boxes
        int num_unknown_mines
        vector[int] mine_indexes
        int game_status
        int num_steps
        int num_random_steps
        double time_used
        int display_mode
        int record_mode
        double sleep_per_step_if_displayed
        vector[int] step_index_list
        vector[int] step_mode_list
        int console_cols
        int console_lines
        
        Interface(int, int, int, int, int, double)
        void re_initialize()
        void prepare_console(int, int)
        void run()
        void terminate_process()

    cdef cppclass ConsoleTools:
        void print_with_color(string, int)
        void set_console_size_to_default()
        void print_at(pair[int, int], string, int)
        void print_in_line(int, string, int)
        void print_copyright_str()
