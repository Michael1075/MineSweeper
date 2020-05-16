import tkinter as tk
from tkinter import messagebox
import tkinter.font as tkFont
import numpy as np
import copy
import time
root = tk.Tk()
val_numrow, val_numcolumn, val_nummine = 1, 1, 0

class Core:
    def __init__(self, numrow, numcolumn, nummine):
        self.numrow = numrow
        self.numcolumn = numcolumn
        self.nummine = nummine
        self.area = numrow * numcolumn
        self.fullmap = np.zeros(self.area, dtype='int8')
        self.viewmap = np.ones(self.area, dtype='int8') * 9
        self.mode = 0
        
    def order(self, x, y):
        n = x * self.numcolumn
        n += y
        return n
        
    def re_order(self, n):
        x = n // self.numcolumn
        y = n % self.numcolumn
        return np.array([x, y], dtype='int64')
        
    def count(self, arr, target):
        counting = 0
        for i in arr:
            if i == target:
                counting += 1
        return counting
        
    def neighbour(self, n):
        neighbourhood = np.array([], dtype='int8')
        x = int(self.re_order(n)[0])
        y = int(self.re_order(n)[1])
        for i in range(x-1, x+2):
            for j in range(y-1, y+2):
                if i in range(self.numrow) and j in range(self.numcolumn):
                    neighbourhood = np.append(neighbourhood, self.order(i, j))
        return neighbourhood

class StopWatch(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.msec = 50
        self._start = 0.0
        self._elapsedtime = 0.0
        self._running = False
        self.timestr = tk.StringVar()
        self._setTime(self._elapsedtime)

    def _update(self):
        self._elapsedtime = time.time() - self._start
        self._setTime(self._elapsedtime)
        self._timer = self.after(self.msec, self._update)

    def _setTime(self, elap):
        minutes = int(elap / 60)
        seconds = int(elap - minutes * 60.0)
        hseconds = int((elap - minutes * 60.0 - seconds) * 100)
        self.timestr.set('%02d\'%02d\"%02d' % (minutes, seconds, hseconds))

    def start(self):
        if not self._running:
            self._start = time.time() - self._elapsedtime
            self._update()
            self._running = True

    def stop(self):
        if self._running:
            self.after_cancel(self._timer)
            self._elapsedtime = time.time() - self._start
            self._setTime(self._elapsedtime)
            self._running = False

class Settings:
    def __init__(self):
        pass

    def open_settings(self):
        self.settings_root = tk.Toplevel()
        self.settings_root.title('Settings')
        self.var = tk.StringVar()
        tk.Label(self.settings_root, text='Default', width=10, anchor='w').grid(row=0, column=0, columnspan=2, padx=10, pady=10)
        rbtn1 = tk.Radiobutton(self.settings_root, text='Easy', width=7, anchor='w', variable=self.var, value=1)
        rbtn2 = tk.Radiobutton(self.settings_root, text='Medium', width=7, anchor='w', variable=self.var, value=2)
        rbtn3 = tk.Radiobutton(self.settings_root, text='Hard', width=7, anchor='w', variable=self.var, value=3)
        tk.Label(self.settings_root, text='9x9, 10mines', width=13, anchor='w').grid(row=1, column=1, padx=10, pady=10, sticky='W')
        tk.Label(self.settings_root, text='16x16, 40mines', width=13, anchor='w').grid(row=2, column=1, padx=10, pady=10, sticky='W')
        tk.Label(self.settings_root, text='16x30, 99mines', width=13, anchor='w').grid(row=3, column=1, padx=10, pady=10, sticky='W')
        rbtn0 = tk.Radiobutton(self.settings_root, text='User-defined', width=10, anchor='w', variable=self.var, value=0)
        tk.Label(self.settings_root, text='# Rows :', width=10, anchor='w').grid(row=1, column=2, padx=10, pady=10, sticky='W')
        tk.Label(self.settings_root, text='# Columns :', width=10, anchor='w').grid(row=2, column=2, padx=10, pady=10, sticky='W')
        tk.Label(self.settings_root, text='# Mines :', width=10, anchor='w').grid(row=3, column=2, padx=10, pady=10, sticky='W')
        self.entry_numrow = tk.Entry(self.settings_root, width=10)
        self.entry_numcolumn = tk.Entry(self.settings_root, width=10)
        self.entry_nummine = tk.Entry(self.settings_root, width=10)
        self.btn_confirm = tk.Button(self.settings_root, text='Confirm', width=10, command=self.set_game)
        self.btn_cancel = tk.Button(self.settings_root, text='Cancel', width=10, command=self.settings_root.destroy)
        rbtn1.grid(row=1, column=0, padx=10, pady=10)
        rbtn2.grid(row=2, column=0, padx=10, pady=10)
        rbtn3.grid(row=3, column=0, padx=10, pady=10)
        rbtn0.grid(row=0, column=2, columnspan=2, padx=10, pady=10)
        self.entry_numrow.grid(row=2, column=3, padx=10, pady=10)
        self.entry_numcolumn.grid(row=1, column=3, padx=10, pady=10)
        self.entry_nummine.grid(row=3, column=3, padx=10, pady=10)
        self.btn_confirm.grid(row=4, column=0, columnspan=2, pady=10)
        self.btn_cancel.grid(row=4, column=2, columnspan=2, pady=10)

    def first_frame(self):
        self.open_settings()
        self.btn_cancel['text'] = 'Quit'
        self.btn_cancel['command'] = root.quit

    def set_game(self):
        global root, val_numrow, val_numcolumn, val_nummine
        try:
            self.difficulty = int(self.var.get())
        except ValueError:
            tk.messagebox.showerror(title='Error', message='Please choose an option!')
        else:
            if self.difficulty != 0:
                self.settings_root.destroy()
                root.destroy()
                root = tk.Tk()
                if self.difficulty == 1:
                    val_numrow, val_numcolumn, val_nummine = 9, 9, 10
                elif self.difficulty == 2:
                    val_numrow, val_numcolumn, val_nummine = 16, 16, 40
                elif self.difficulty == 3:
                    val_numrow, val_numcolumn, val_nummine = 30, 16, 99
                Main(val_numrow, val_numcolumn, val_nummine, root)
            else:
                try:
                    val_numrow = int(self.entry_numrow.get())
                    val_numcolumn = int(self.entry_numcolumn.get())
                    val_nummine = int(self.entry_nummine.get())
                except ValueError:
                    tk.messagebox.showerror(title='Error', message='Invalid input!')
                else:
                    if val_numrow > 0 and val_numcolumn > 0 and val_nummine >= 0:
                        self.settings_root.destroy()
                        root.destroy()
                        root = tk.Tk()
                        Main(val_numrow, val_numcolumn, val_nummine, root)
                    else:
                        tk.messagebox.showerror(title='Error', message='Invalid input!')

    def renew(self):
        global root, val_numrow, val_numcolumn, val_nummine
        root.destroy()
        root = tk.Tk()
        Main(val_numrow, val_numcolumn, val_nummine, root)

class Main(Core, StopWatch, Settings):
    def __init__(self, numrow, numcolumn, nummine, parent):
        Core.__init__(self, numrow, numcolumn, nummine)
        StopWatch.__init__(self, parent)
        Settings.__init__(self)
        self.parent = parent
        self.buttonmap = []
        self.style = [' 12345678 @xx-', ['Black', 'Blue', 'Green', 'Red', 'Purple', 'Brown', 'Cyan', 'Black', 'Grey', 'Black', 'Yellow', 'Orange', 'Gold', 'Gray']]
        self.display_font = tkFont.Font(family='Helvetica', size=10, weight=tkFont.BOLD)
        self.start_game()
    
    def handlerAdaptor(self, func, **kwds):
        return lambda event, func=func, kwds=kwds: func(event, **kwds)

    def start_game(self):
        self.parent.title('Mine Sweeper')
        menubar = tk.Menu(self.parent)
        options_menu = tk.Menu(menubar, tearoff = 0)
        options_menu.add_command(label='New Game', command=self.renew)
        options_menu.add_command(label='Settings', command=self.open_settings)
        menubar.add_cascade(label='Options', menu=options_menu)
        self.parent.config(menu=menubar)
        vbar = tk.Scrollbar(self.parent, orient='vertical')
        vbar.pack(fill='y', side='right')
        hbar = tk.Scrollbar(self.parent, orient='horizontal')
        hbar.pack(fill='x', side='bottom')
        self.rest_mine = tk.Label(self.parent, text=str(self.num_restmine()))
        self.timer = tk.Label(self.parent, textvariable=self.timestr)
        self.timer.pack(side='top', anchor='e', padx=10)
        self.rest_mine.pack(side='top', anchor='w', padx=10)
        canvas_map = tk.Canvas(self.parent, width=self.numrow*30, height=self.numcolumn*30, scrollregion=(0, 0, self.numrow*30, self.numcolumn*30), xscrollincrement=30, yscrollincrement=30)
        for i in range(self.numrow):
            for j in range(self.numcolumn):
                n = self.order(i, j)
                if self.viewmap[n] in range(9, 13):
                    btn = tk.Button(self.parent, width=2, height=1, text=self.style[0][self.viewmap[n]], fg=self.style[1][self.viewmap[n]], bg='Blue', activebackground='RoyalBlue', relief='groove', font=self.display_font)
                else:
                    btn = tk.Button(self.parent, width=2, height=1, text=self.style[0][self.viewmap[n]], fg=self.style[1][self.viewmap[n]], bg='LightCyan', activebackground='Azure', relief='groove', font=self.display_font)
                btn.bind('<ButtonRelease-1>', self.handlerAdaptor(self.First, n=n))
                self.buttonmap.append(btn)
                canvas_map.create_window(30 * i, 30 * j, anchor='nw', window=btn)
        canvas_map.pack(anchor='nw', expand=True, padx=30, pady=30)
        vbar.config(command=canvas_map.yview)
        hbar.config(command=canvas_map.xview)
        self.parent.mainloop()

    def end_game(self):
        self.stop()
        for i in range(self.area):
            self.buttonmap[i].bind('<ButtonRelease-1>', lambda i: None)
            self.buttonmap[i].bind('<ButtonRelease-3>', lambda i: None)
        if self.mode == 2:
            tk.messagebox.showinfo(title='Result', message='Congratulations! You\'ve won this game!\nYou ended this game in %ss.' % (int(self._elapsedtime * 100) / 100))
        else:
            tk.messagebox.showinfo(title='Result', message='Oops! You\'ve lost this game!\nYou ended this game in %ss.' % (int(self._elapsedtime * 100) / 100))
        ask = tk.messagebox.askyesno(title="Retry", message="Do you want to play another time?")
        if ask == True:
            self.renew()

    def update_map(self, n):
        self.buttonmap[n].configure(text=self.style[0][self.viewmap[n]], fg=self.style[1][self.viewmap[n]])
        if self.viewmap[n] not in range(9, 13):
            self.buttonmap[n].configure(bg='LightCyan', activebackground='Azure')

    def update_restmine(self):
        self.rest_mine.configure(text=str(self.num_restmine()))

    def num_restmine(self):
        return self.nummine - self.count(self.viewmap, 10)

    def first(self, n):
        choices = np.setdiff1d(np.arange(self.area), self.neighbour(n))
        try:
            mine_location = np.random.choice(choices, self.nummine, replace=False)
        except ValueError:
            ask = tk.messagebox.askyesno(title='Error', message='Failed to form a mine map!\nChange settings?')
            if ask == True:
                self.open_settings()
        else:
            self.start()
            for i in mine_location:
                self.fullmap[i] = -1
            for i in range(self.area):
                if self.fullmap[i] != -1:
                    for j in self.neighbour(i):
                        if self.fullmap[j] == -1:
                            self.fullmap[i] += 1
            self.mode = 1

    def First(self, event, n):
        self.first(n)
        self.Explore(event, n)
        if self.mode == 1:
            for i in range(self.area):
                self.buttonmap[i].bind('<ButtonRelease-1>', self.handlerAdaptor(self.Explore, n=i))
                self.buttonmap[i].bind('<ButtonRelease-3>', self.handlerAdaptor(self.Flag, n=i))

    def flag(self, n):
        if self.viewmap[n] == 9:
            self.viewmap[n] = 10
        elif self.viewmap[n] == 10:
            self.viewmap[n] = 9

    def Flag(self, event, n):
        self.flag(n)
        self.update_map(n)
        self.update_restmine()

    def single_explore(self, n):
        self.viewmap[n] = self.fullmap[n]
        self.update_map(n)

    def zero_expand(self, n):
        for i in self.neighbour(n):
            self.single_explore(i)

    def explore(self, n):
        if self.mode == 1:
            if self.fullmap[n] == -1:
                self.mode = 3
                self.viewmap[n] = 11
                self.update_map(n)
                for i in range(self.area):
                    if self.fullmap[i] == -1 and self.viewmap[i] == 9:
                        self.viewmap[i] = 12
                        self.update_map(i)
                    elif self.fullmap[i] != -1 and self.viewmap[i] == 10:
                        self.viewmap[i] = 13
                        self.update_map(i)
            else:
                if self.viewmap[n] == 9:
                    if self.fullmap[n] == 0:
                        new_zeros = np.array([n])
                        while np.size(new_zeros) != 0:
                            zero_num = np.size(new_zeros)
                            oldmap = copy.copy(self.viewmap)
                            for i in new_zeros:
                                self.zero_expand(i)
                            newmap = copy.copy(self.viewmap)
                            for i in new_zeros:
                                for j in self.neighbour(i):
                                    if j not in new_zeros:
                                        if newmap[j] == 0 and oldmap[j] != 0:
                                            new_zeros = np.append(new_zeros, j)
                            new_zeros = new_zeros[zero_num::]
                    else:
                        self.single_explore(n)
                if self.count(self.viewmap, 9) + self.count(self.viewmap, 10) == self.nummine:
                    self.mode = 2
                    for i in range(self.area):
                        if self.viewmap[i] == 9:
                            self.viewmap[i] = 10
                            self.update_map(i)
                            self.update_restmine()

    def Explore(self, event, n):
        if self.mode == 1 and self.viewmap[n] in range(1, 9):
            counting1 = 0
            for i in self.neighbour(n):
                if self.viewmap[i] == 10:
                    counting1 += 1
            if self.viewmap[n] == counting1:
                counting2 = 0
                for i in self.neighbour(n):
                    if self.fullmap[i] == -1 and self.viewmap[i] == 9:
                        counting2 += 1
                if counting2 == 0:
                    for i in self.neighbour(n):
                        if self.viewmap[i] == 9:
                            self.explore(i)
                    self.update_map(i)
                else:
                    self.mode = 3
                    for i in self.neighbour(n):
                        if self.fullmap[i] == -1 and self.viewmap[i] == 9:
                            self.viewmap[i] = 11
                            self.update_map(i)
                    for i in range(self.area):
                        if self.fullmap[i] == -1 and self.viewmap[i] == 9:
                            self.viewmap[i] = 12
                            self.update_map(i)
                        elif self.fullmap[i] != -1 and self.viewmap[i] == 10:
                            self.viewmap[i] = 13
                            self.update_map(i)
        else:
            self.explore(n)
        if self.mode == 2 or self.mode == 3:
            self.end_game()

class Progress(Main):
    def __init__(self, parent):
        self.first_frame()
        parent.withdraw()
        Settings.__init__(self)
        Main.__init__(self, 1, 1, 0, parent)

if __name__ == '__main__':
    Progress(root)