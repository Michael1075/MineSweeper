# distutils: language=c++

from cpp_ext cimport cpp_main
from cpp_ext cimport ConsoleTools


cpdef py_main(int mw, int mh, int nm, int ng, int rm, int uf):
    cpp_main(mw, mh, nm, ng, rm, uf)


cdef class PyConsoleTools:
    cdef ConsoleTools *thisptr

    def __cinit__(self):
        self.thisptr = new ConsoleTools()

    def __dealloc__(self):
        del self.thisptr

    def clear_console(self):
        self.thisptr.clear_console()

    def printf_with_color(self, str value, int color):
        self.thisptr.printf_with_color(value.encode(), color)

    def set_console_size_to_default(self):
        self.thisptr.set_console_size_to_default()
