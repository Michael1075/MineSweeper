#ifndef _TOOLS_H
#define _TOOLS_H

#include <algorithm>
#include <assert.h>
#include <iostream>
#include <string>
#include <vector>
#include <windows.h>

#ifndef __author__
#define __author__ "Michael W"
#endif


using namespace std;
typedef pair<int, int> COORD_T;


static const string COPYRIGHT_STR("cy_autosweeper.py - by Michael W");


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


const bool contains(const string &substr, const string &str) {
	return str.find(substr) != string::npos;
}


const string repeat_str(int repeat_times, const string &str) {
	string result;
	for (int _ = 0; _ < repeat_times; ++_) {
		result += str;
	}
	return result;
}


const double get_current_time() {
	LARGE_INTEGER n_freq, current_time;
	QueryPerformanceFrequency(&n_freq);
	QueryPerformanceCounter(&current_time);
	return static_cast<double>(current_time.QuadPart) / n_freq.QuadPart;
}


string set_space(const string &str, int str_length, int align) {
	/**
	 *:param align: int in range(-1, 2)
	 *    -1: align at left side
	 *    0: align at center
	 *    1: align at right side
	 */
	int spaces(str_length - static_cast<int>(str.size()));
	if (spaces <= 0) {
		return str;
	}
	string result;
	switch (align) {
		case 1: {
			for (int _ = 0; _ < spaces; ++_) {
				result += ' ';
			}
			result += str;
			break;
		}
		case 0: {
			for (int _ = 0; _ < spaces / 2; ++_) {
				result += ' ';
			}
			result += str;
			for (int _ = 0; _ < spaces - spaces / 2; ++_) {
				result += ' ';
			}
			break;
		}
		case -1: {
			result += str;
			for (int _ = 0; _ < spaces; ++_) {
				result += ' ';
			}
			break;
		}
	}
	return result;
}


struct RandomTools {
public:
	RandomTools() = default;
	~RandomTools() = default;

	const int randint(int range_maximum) const {
		return rand() % range_maximum;
	}

	const int random_choice(vector<int> vals) const {
		return random_choices(vals, 1)[0];
	}

	const vector<int> random_choices(vector<int> vals, int num_choices) const {
		vector<int> result(num_choices);
		int vals_size(static_cast<int>(vals.size()));
		for (int i = 0; i < num_choices; ++i) {
			int rand_index = randint(vals_size - i);
			int choosed_vals = vals[rand_index];
			vals.erase(vals.begin() + rand_index);
			result[i] = choosed_vals;
		}
		return result;
	}
};


HANDLE hStdOut(GetStdHandle(STD_OUTPUT_HANDLE));

const BOOL set_console_cursor_position(int x, int y) {
	COORD coord = {static_cast<SHORT>(x), static_cast<SHORT>(y)};
	return SetConsoleCursorPosition(hStdOut, coord);
}

const BOOL set_console_cursor_info(bool cursor_visible, int cursor_size) {
	DWORD dwSize(cursor_size);
	BOOL bVisible(cursor_visible);
	const CONSOLE_CURSOR_INFO console_cursor_info = {dwSize, bVisible};
	const CONSOLE_CURSOR_INFO *console_cursor_info_p;
	console_cursor_info_p = &console_cursor_info;
	return SetConsoleCursorInfo(hStdOut, console_cursor_info_p);
}

const BOOL set_console_text_attribute(int color) {
	return SetConsoleTextAttribute(hStdOut, color);
}


struct ConsoleTools {
public:
	static const int DEFAULT_CONSOLE_COLS;
	static const int DEFAULT_CONSOLE_LINES;
	static const int DEFAULT_DW_SIZE;
	int __cols;
	int __lines;

	ConsoleTools():
		__cols(DEFAULT_CONSOLE_COLS),
		__lines(DEFAULT_CONSOLE_LINES)
	{}

	~ConsoleTools() {}

	void clear_console() const {
		system("cls");
	}

	void hide_cursor(int cursor_size=DEFAULT_DW_SIZE) const {
		set_console_cursor_info(0, cursor_size);
	}

	void show_cursor(int cursor_size=DEFAULT_DW_SIZE) const {
		set_console_cursor_info(1, cursor_size);
	}

	void __set_cmd_text_color(int color) const {
		set_console_text_attribute(color);
	}

	void __reset_color() const {
		__set_cmd_text_color(0x0f);
	}

	void print_with_color(const string &value, int color) const {
		__set_cmd_text_color(color);
		cout << value << flush;
		__reset_color();
	}

	void __set_console_size() const {
		string cmd_str("mode con cols=" + to_string(__cols + 3) + " lines=" + to_string(__lines + 2));
		system(cmd_str.c_str());
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

	void __move_cursor_to(COORD_T coord) const {
		int x(coord.first);
		int y(coord.second);
		assert(x < __cols && y < __lines);
		set_console_cursor_position(x, y);
	}

	void print_at(COORD_T coord, const string &value, int color=0x0f) const {
		assert(!contains("\n", value));
		assert(static_cast<int>(value.size()) + coord.first <= __cols);
		__move_cursor_to(coord);
		print_with_color(value, color);
	}

	void print_in_line(int line_index, const string &value, int color=0x0f) const {
		print_at({0, line_index}, value, color);
	}

	void print_list_as_table_row(int line_index, const vector<string> &strs, int cell_width, int align, const string &cell_separator) const {
		if (!strs.size()) {
			return;
		}
		string line_str;
		for (int i = 0; i < strs.size() - 1; ++i) {
			line_str += set_space(strs[i], cell_width, align) + cell_separator;
		}
		line_str += set_space(strs.back(), cell_width, align);
		print_in_line(line_index, line_str);
	}

	void print_copyright_str() const {
		print_in_line(0, COPYRIGHT_STR);
	}

	void print_at_end(int reversed_line_index, string val, int color=0x0f) const {
		int line_index(__lines - reversed_line_index - 1);
		print_in_line(line_index, val, color);
	}

	void ready_to_quit() {
		print_at_end(0, "Press any key to quit...");
		show_cursor();
		system("pause > nul");
		clear_console();
		set_console_size_to_default();
		exit(0);
	}
};


const int ConsoleTools::DEFAULT_CONSOLE_COLS(80);
const int ConsoleTools::DEFAULT_CONSOLE_LINES(40);
const int ConsoleTools::DEFAULT_DW_SIZE(20);


#endif
