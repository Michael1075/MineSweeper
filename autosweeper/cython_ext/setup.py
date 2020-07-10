from Cython.Build import cythonize
from distutils.extension import Extension
from distutils.core import setup

setup(
    ext_modules=cythonize(
        [
            Extension(
                "ext",
                ["ext.pyx"],
            )
        ],
        language_level="3"
    )
)
