#ifndef _TOOLS_H
#define _TOOLS_H

#include <algorithm>
#include <assert.h>
#include <direct.h>
#include <fstream>
#include <vector>
#include <windows.h>

#if !defined(_WIN32)
#include <conio.h>
#endif


using namespace std;


static const char *COPYRIGHT_STR("cpp_autosweeper.cpp - by Michael W");


double f_div(int a, int b) {
	if (b == 0) {
		return 0.0;
	}
	return static_cast<double>(a) / b;
}


double f_div(double a, int b) {
	if (b == 0) {
		return 0.0;
	}
	return a / b;
}


const int max_of(initializer_list<int> vals) {
	if (!vals.size()) {
		return 0;
	}
	int result(*vals.begin());
	for (auto iter = vals.begin() + 1; iter != vals.end(); ++iter) {
		result = max(result, *iter);
	}
	return result;
}


const bool contains(int num, const vector<int> &vals) {
	return find(vals.cbegin(), vals.cend(), num) != vals.cend();
}


const bool contains(int num, const vector<int> &vals, vector<int>::const_iterator &find_result) {
	find_result = find(vals.cbegin(), vals.cend(), num);
	return find_result != vals.cend();
}


const double get_current_time() {
	LARGE_INTEGER n_freq, current_time;
	QueryPerformanceFrequency(&n_freq);
	QueryPerformanceCounter(&current_time);
	return static_cast<double>(current_time.QuadPart) / n_freq.QuadPart;
}


namespace random {
const int randint(int range_maximum) {
	return rand() % range_maximum;
}

const int random_choice(vector<int> vals) {
	int vals_size(static_cast<int>(vals.size()));
	int rand_index = randint(vals_size);
	return vals[rand_index];
}

const vector<int> random_choices(vector<int> vals, int num_choices) {
	vector<int> result(num_choices);
	int vals_size(static_cast<int>(vals.size()));
	int rand_index, chosen_val;
	for (int i = 0; i < num_choices; ++i) {
		rand_index = randint(vals_size - i);
		chosen_val = vals[rand_index];
		vals.erase(vals.begin() + rand_index);
		result[i] = chosen_val;
	}
	return result;
}
}


namespace os {
const bool exists(const char *path) {
	return _access(path, 0) == 0;
}

const int count_num_files(const char *path) {
	char file_path[64];
	sprintf(file_path, "%s\\0.json", path);
	if (!exists(file_path)) {
		return 0;
	}
	sprintf(file_path, "%s\\1.json", path);
	if (!exists(file_path)) {
		return 1;
	}
	int upper_bound(1);
	bool current_file_exists(true);
	while (current_file_exists) {
		upper_bound *= 2;
		sprintf(file_path, "%s\\%d.json", path, upper_bound);
		current_file_exists = exists(file_path);
	}
	int lower_bound(upper_bound / 2);
	int middle((lower_bound + upper_bound) / 2);
	while (middle != lower_bound) {
		sprintf(file_path, "%s\\%d.json", path, middle);
		if (exists(file_path)) {
			lower_bound = middle;
		} else {
			upper_bound = middle;
		}
		middle = (lower_bound + upper_bound) / 2;
	}
	return middle + 1;
}

void make_dir(const char *folder_path) {
	if (!exists(folder_path)) {
		_mkdir(folder_path);
	}
}
}


struct ConsoleTools {
private:
	int __cols;
	int __lines;
	HANDLE __hStdOut;

	const BOOL __set_console_cursor_position(int x, int y) const {
		COORD coord = {static_cast<SHORT>(x), static_cast<SHORT>(y)};
		return SetConsoleCursorPosition(__hStdOut, coord);
	}
	
	const BOOL __set_console_cursor_info(bool cursor_visible, int cursor_size) const {
		DWORD dwSize(cursor_size);
		BOOL bVisible(cursor_visible);
		const CONSOLE_CURSOR_INFO console_cursor_info = {dwSize, bVisible};
		const CONSOLE_CURSOR_INFO *console_cursor_info_p;
		console_cursor_info_p = &console_cursor_info;
		return SetConsoleCursorInfo(__hStdOut, console_cursor_info_p);
	}
	
	const BOOL __set_console_text_attribute(int color) const {
		return SetConsoleTextAttribute(__hStdOut, color);
	}

	void __set_console_size() const {
		char cmd_str[64];
		sprintf(cmd_str, "mode con cols=%d lines=%d", __cols + 3, __lines + 2);
		system(cmd_str);
	}

public:
	static const int DEFAULT_CONSOLE_COLS = 80;
	static const int DEFAULT_CONSOLE_LINES = 40;
	static const int DEFAULT_DW_SIZE = 20;

	ConsoleTools():
		__cols(DEFAULT_CONSOLE_COLS),
		__lines(DEFAULT_CONSOLE_LINES),
		__hStdOut(GetStdHandle(STD_OUTPUT_HANDLE))
	{}

	virtual ~ConsoleTools() = default;

	void clear_console() const {
		system("cls");
	}

	void hide_cursor(int cursor_size=DEFAULT_DW_SIZE) const {
		__set_console_cursor_info(0, cursor_size);
	}

	void show_cursor(int cursor_size=DEFAULT_DW_SIZE) const {
		__set_console_cursor_info(1, cursor_size);
	}

	void set_cmd_text_color(int color) const {
		__set_console_text_attribute(color);
	}

	void reset_color() const {
		set_cmd_text_color(0x0f);
	}

	void printf_with_color(const char *value, int color) const {
		set_cmd_text_color(color);
		printf(value);
		reset_color();
	}
	
	void set_console_size(int cols, int lines) {
		__cols = cols;
		__lines = lines;
		__set_console_size();
	}
	
	void set_console_size_to_default() {
		__cols = DEFAULT_CONSOLE_COLS;
		__lines = DEFAULT_CONSOLE_LINES;
		__set_console_size();
	}

	void move_cursor_to(pair<int, int> coord) const {
		int x(coord.first);
		int y(coord.second);
		assert(x < __cols && y < __lines);
		__set_console_cursor_position(x, y);
	}

	void move_cursor_to_line(int line_index) const {
		move_cursor_to({0, line_index});
	}

	void move_cursor_to_end_line(int reversed_line_index) const {
		move_cursor_to_line(__lines - reversed_line_index - 1);
	}

	void pause() {
		printf("Press any key to continue...");
#if defined(_WIN32)
		system("pause > nul");
#else
		getch();
#endif
	}

	void ready_to_begin(int cols, int lines) {
		clear_console();
		hide_cursor();
		reset_color();
		set_console_size(cols, lines);
	}

	void ready_to_quit() {
		show_cursor();
		move_cursor_to_end_line(0);
		pause();
		clear_console();
		set_console_size_to_default();
		exit(0);
	}
} CONSOLE;


#endif
