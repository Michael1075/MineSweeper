# MineSweeper

*A collection of all MineSweeper projects*

| file/folder name    | language                | last update | status  |
| :-----------------: | :---------------------: | :---------: | :-----: |
| `charsweeper.py`    | python                  | 2018/12/22  | frozen  |
| `minesweeper_tk.py` | python                  | 2019/2/13   | frozen  |
| `minesweeper_js`    | javascript & html & css | 2020/4/4    | frozen  |
| `autosweeper`       | python & Cython & C++   | 2020/7/10   | ongoing |

## `charsweeper.py`

*Let the computer play MineSweeper game automatically on the console*

There remains some bugs, and usually cannot run completely. **You had better NOT run this file.**

I wrote this project when I was just begining to learn programming. Most of it was written in the summer holiday in 2018. I even didn't follow PEP-8 programming standard. The code cannot be worse both in style and in algorithm---it contains an algorithm with exponent-time complexity, causing jams. This file lives here as a kind of commemoration, never to be updated.

## `minesweeper_tk.py`

*MineSweeper game written in python based on tkinter module*

Note, if the map is too big, every updating step (especially initializing) will probably cause the processing to slow down.

It's a project for me to learn OOP programming in early time, and thus the code is still complicated. After all, it's a successful project and gave me much confidence at that time.

## `minesweeper_js`

*MineSweeper game written in javascript*

To play MineSweeper, you may simply run `mine_sweeper.html` in `minesweeper_js` folder.

This is my first javascript project.

## `autosweeper`

*Let computer play MineSweeper automatically*

You may run `python autosweeper.py` and follow the instructions. Games played can be recorded as json files and saved in `game_savings` folder, and these files can be read and displayed in the future. The `numpy` package is no longer necessary, so using pypy to run `autosweeper.py` is allowed.

Cython version has been completed. You can run `cy_autosweeper.py`, where the logic part is completed by C++ extensions. By introducing Cython, it would be more possible and easier to improve the algorithm.

Note: `cython_ext/cpp_ext.cpp` can be compiled as well. You should add the command `-fexec-charset=GBK` if you want to compile it yourself.

Pure C++ version hasn't been completed yet. Still updating.

A speed test made on 2020/7/10 (30 * 16, 99 mines, average on 10000 loops, updating every 100 loops, without showing map):

| language                     | avg. time (ms) | avg. time (won) (ms) |
| :--------------------------: | -------------: | -------------------: |
| CPython                      |      47.182692 |            49.679944 |
| PyPy (with jit)              |      11.875926 |            13.942982 |
| Cython (with C++ extensions) |       2.286285 |             2.553813 |
| C++                          |              ? |                    ? |
| C++ (with multiprocessing)   |              ? |                    ? |

## License

Copyright (c) 2020-present Michael W, released under the MIT license.

## Thanks

Great thanks to those who have helped or inspired me more or less during the production of this repository.

[@wlt233](https://github.com/wlt233)  
[@ArbitSV](https://github.com/ArbitSV)  
[@Jiangzemin1926](https://github.com/Jiangzemin1926/Minesweeper)  
[@RainbowRoad1](https://github.com/RainbowRoad1/Cgame)  
[@ztxz16](https://github.com/ztxz16/Mine)

