# distutils: language=c++

cdef extern from "cpp_autosweeper.cpp":
    cpdef void cpp_main(int, int, int, int, int, int)

    cdef cppclass ConsoleTools:
        void clear_console()
        void printf_with_color(char*, int)
        void set_console_size_to_default()
