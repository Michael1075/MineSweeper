#include "cpp_ext.h"

#ifndef __author__
#define __author__ "Michael W"
#endif


using namespace std;


ConsoleTools CONSOLE;


Core::Core(int mw, int mh, int nm):
	map_width(mw),
	map_height(mh),
	num_mines(nm),
	num_boxes(mw * mh),
	num_unknown_boxes(num_boxes),
	num_unknown_mines(nm),
	mine_indexes(vector<int>(nm, -1)),
	base_map(vector<int>(num_boxes, 0)),
	view_map(vector<int>(num_boxes, 9)),

	game_status(0),
	num_steps(0),
	num_random_steps(0),
	previous_index(0),
	time_used(0.0),

	surrounding_indexes(vector<vector<int>>(num_boxes)),
	sub_surrounding_indexes(vector<vector<int>>(num_boxes)),

	trace_lock(false),
	layer(0),
	x0(0),
	y0(0),
	dx(0),
	dy(0),
	next_coord(coord_t()),
	next_index(0)
{
	srand((unsigned)time(NULL));
	init_surrounding_indexes();
}

Core::~Core() = default;

void Core::init_surrounding_indexes() {
	for (int i = 0; i < num_boxes; ++i) {
		surrounding_indexes[i] = get_surrounding_indexes(i);
		sub_surrounding_indexes[i] = get_surrounding_indexes(i, 2);
	}
}

void Core::re_initialize() {
	num_unknown_boxes = num_boxes;
	num_unknown_mines = num_mines;
	mine_indexes.assign(num_mines, -1);
	base_map.assign(num_boxes, 0);
	view_map.assign(num_boxes, 9);

	game_status = 0;
	num_steps = 0;
	num_random_steps = 0;
	previous_index = 0;
	time_used = 0.0;

	trace_lock = false;
	layer = 0;
	x0 = 0;
	y0 = 0;
	dx = 0;
	dy = 0;
	next_coord = {0, 0};
	next_index = 0;
}

const vector<int> Core::get_union(const vector<int> &list0, const vector<int> &list1) const {
	vector<int> result;
	result.reserve(min(list0.size(), list1.size()));
	for (int i : list0) {
		if (contains(i, list1)) {
			result.push_back(i);
		}
	}
	return result;
}

const vector<int> Core::get_difference(const vector<int> &list0, const vector<int> &list1) const {
	vector<int> result;
	result.reserve(list0.size());
	for (int i : list0) {
		if (!contains(i, list1)) {
			result.push_back(i);
		}
	}
	return result;
}

const int Core::coord_to_index(const coord_t &coord) const {
	return coord.first + map_width * coord.second;
}

const coord_t Core::index_to_coord(int index) const {
	return coord_t(index % map_width, index / map_width);
}

const bool Core::in_map(const coord_t &coord) const {
	int x(coord.first);
	int y(coord.second);
	return 0 <= x && x < map_width && 0 <= y && y < map_height;
}

void Core::set_spiral_trace_generator(int center_index, int l) {
	assert(!trace_lock);
	trace_lock = true;
	layer = l;
	x0 = center_index % map_width;
	y0 = center_index / map_width;
	dx = 0;
	dy = 0;
	coord_t next_coord = index_to_coord(center_index);
	if (l == -1) {
		layer = max_of({x0, map_width - x0 - 1, y0, map_height - y0 - 1});
	}
	next_index = center_index;
}

void Core::move_to_next_index() {
	do {
		if (dx + dy <= 0 && dx - dy >= 0) {
			++dx;
		} else if (dx + dy > 0 && dx - dy <= 0) {
			--dx;
		} else if (dx + dy > 0 && dx - dy > 0) {
			++dy;
		} else if (dx + dy <= 0 && dx - dy < 0) {
			--dy;
		}
		if (max(abs(dx), abs(dy)) > layer) {
			next_index = -1;
			return;
		}
		next_coord = {x0 + dx, y0 + dy};
	} while (!in_map(next_coord));
	next_index = coord_to_index(next_coord);
}

void Core::unlock_spiral_trace_generator() {
	assert(trace_lock);
	trace_lock = false;
}

const vector<int> Core::get_surrounding_indexes_with_self(int index, int layer) {
	vector<int> result;
	result.reserve(min((2 * layer + 1) * (2 * layer + 1), num_boxes));
	set_spiral_trace_generator(index, layer);
	while (next_index != -1) {
		result.push_back(next_index);
		move_to_next_index();
	}
	unlock_spiral_trace_generator();
	return result;
}

const vector<int> Core::get_surrounding_indexes(int index, int layer) {
	vector<int> result(get_surrounding_indexes_with_self(index, layer));
	result.erase(result.begin());
	return result;
}

const vector<int> Core::get_common_indexes(int index0, int index1) const {
	vector<int> surrounding0(surrounding_indexes[index0]);
	vector<int> surrounding1(surrounding_indexes[index1]);
	vector<int> result(get_union(surrounding0, surrounding1));
	return result;
}

const vector<int> Core::get_suburb_indexes(int index0, int index1) const {
	vector<int> surrounding0(surrounding_indexes[index0]);
	vector<int> surrounding1(surrounding_indexes[index1]);
	vector<int> result(get_difference(surrounding0, surrounding1));
	return result;
}

const vector<int> Core::indexes_ordered_in_spiral(int index, vector<int> index_list) {
	set_spiral_trace_generator(index);
	vector<int> result;
	result.reserve(index_list.size());
	vector<int>::const_iterator find_result;
	while (index_list.size()) {
		if (contains(next_index, index_list, find_result)) {
			index_list.erase(find_result);
			result.push_back(next_index);
		}
		move_to_next_index();
	}
	unlock_spiral_trace_generator();
	return result;
}

void Core::init_mine_indexes(int first_index) {
	vector<int> safe_region_indexes(get_surrounding_indexes_with_self(first_index));
	vector<int> map_index_choices;
	map_index_choices.reserve(num_boxes);
	for (int i = 0; i < num_boxes; ++i) {
		if (!contains(i, safe_region_indexes)) {
			map_index_choices.push_back(i);
		}
	}
	if (map_index_choices.size() < num_mines) {
		raise_init_mine_map_error();
	}
	mine_indexes = random_choices(map_index_choices, num_mines);
}

void Core::init_base_map() {
	for (int mine_index : mine_indexes) {
		base_map[mine_index] = -1;
	}
	for (int mine_index : mine_indexes) {
		for (int i : surrounding_indexes[mine_index]) {
			if (base_map[i] != -1) {
				++base_map[i];
			}
		}
	}
}

void Core::reduce_num_unknown_boxes() {
	--num_unknown_boxes;
}

void Core::reduce_num_unknown_mines() {
	--num_unknown_mines;
}

void Core::expand_zero(int index) {
	vector<int> pre_updated_zero_region;
	vector<int> zero_region {index};
	vector<int> zero_region_difference;
	while (pre_updated_zero_region.size() != zero_region.size()) {
		zero_region_difference = get_difference(zero_region, pre_updated_zero_region);
		pre_updated_zero_region = zero_region;
		for (int i : zero_region_difference) {
			for (int j : surrounding_indexes[i]) {
				if (base_map[j] == 0 && !contains(j, zero_region)) {
					zero_region.push_back(j);
				}
			}
		}
	}
	vector<int> expand_region(zero_region);
	for (int i : zero_region) {
		for (int j : surrounding_indexes[i]) {
			if (view_map[j] == 9 && !contains(j, expand_region)) {
				expand_region.push_back(j);
			}
		}
	}
	for (int i : indexes_ordered_in_spiral(index, expand_region)) {
		explore_single_safe_box(i);
	}
}

void Core::explore_single_safe_box(int index) {
	reduce_num_unknown_boxes();
	view_map[index] = base_map[index];
	update_map(index);
}

void Core::explore_surrounding(int index) {
	vector<int> indexes(surrounding_indexes[index]);
	int flags_count(0);
	for (int i : indexes) {
		if (view_map[i] == 10) {
			++flags_count;
		}
	}
	if (flags_count == base_map[index]) {
		vector<int> surrounding_mine_indexes;
		for (int i : indexes) {
			if (base_map[i] == -1 && view_map[i] != 10) {
				surrounding_mine_indexes.push_back(i);
			}
		}
		if (surrounding_mine_indexes.size()) {
			explode(surrounding_mine_indexes);
		} else {
			for (int i : indexes) {
				if (view_map[i] == 9) {
					explore_blank_box(i);
				}
			}
		}
	}
}

void Core::explore_blank_box(int index) {
	switch (base_map[index]) {
		case -1: {
			explode({index});
			break;
		}
		case 0: {
			expand_zero(index);
			break;
		}
		default: {
			explore_single_safe_box(index);
		}
	}
}

void Core::flag_blank_box(int index) {
	view_map[index] = 10;
	reduce_num_unknown_boxes();
	reduce_num_unknown_mines();
	update_map(index);
}

void Core::exploit_step(const step_t &step) {
	++num_steps;
	int index(step.first);
	int step_mode(step.second);
	switch (step_mode) {
		case 0: {
			explore_blank_box(index);
			break;
		}
		case 1: {
			explore_surrounding(index);
			break;
		}
		case 2: {
			flag_blank_box(index);
			break;
		}
		case 3: {
			++num_random_steps;
			explore_blank_box(index);
			break;
		}
	}
	check_if_win();
}

void Core::start(int first_index) {
	init_mine_indexes(first_index);
	init_base_map();
	game_status = 1;
}

void Core::explode(const vector<int> &indexes) {
	set_spiral_trace_generator(previous_index);
	for (int _ = 0; _ < num_boxes; ++_) {
		if (contains(next_index, indexes)) {
			view_map[next_index] = 11;
		} else if (base_map[next_index] == -1 && view_map[next_index] != 10) {
			view_map[next_index] = 12;
		} else if (base_map[next_index] != -1 && view_map[next_index] == 10) {
			view_map[next_index] = 13;
		} else {
			move_to_next_index();
			continue;
		}
		update_map(next_index);
		move_to_next_index();
	}
	unlock_spiral_trace_generator();
	game_status = 3;
}

void Core::win() {
	set_spiral_trace_generator(previous_index);
	for (int _ = 0; _ < num_boxes; ++_) {
		if (view_map[next_index] == 9) {
			flag_blank_box(next_index);
		}
		update_map(next_index);
		move_to_next_index();
	}
	unlock_spiral_trace_generator();
	game_status = 2;
}

void Core::check_if_win() {
	int mines_count(static_cast<int>(count(view_map.cbegin(), view_map.cend(), 9)));
	if (game_status == 1 && mines_count == num_unknown_mines) {
		win();
	}
}

void Core::run() {
	double begin_time(get_current_time());
	on_playing();
	double end_time(get_current_time());
	time_used = end_time - begin_time;
}


Logic::Logic(int mw, int mh, int nm):
	Core(mw, mh, nm),
	unknown_map(vector<int>(num_boxes)),
	flags_map(vector<int>(num_boxes)),
	cached_steps(list<step_t>())
{
	init_unknown_map();
}

void Logic::init_unknown_map() {
	for (int i = 0; i < num_boxes; ++i) {
		unknown_map[i] = static_cast<int>(surrounding_indexes[i].size());
	}
}

void Logic::re_initialize() {
	Core::re_initialize();
	unknown_map.assign(num_boxes, 0);
	flags_map.assign(num_boxes, 0);
	cached_steps.clear();
	init_unknown_map();
}

void Logic::modify_surrounding_unknown_map(int index) {
	for (int i : surrounding_indexes[index]) {
		--unknown_map[i];
	}
}

void Logic::modify_surrounding_flags_map(int index) {
	for (int i : surrounding_indexes[index]) {
		++flags_map[i];
	}
}

void Logic::explore_single_safe_box(int index) {
	Core::explore_single_safe_box(index);
	modify_surrounding_unknown_map(index);
}

void Logic::flag_blank_box(int index) {
	Core::flag_blank_box(index);
	modify_surrounding_unknown_map(index);
	modify_surrounding_flags_map(index);
}

const bool Logic::is_valuable(int index) const {
	return unknown_map[index] != 0 && view_map[index] < 9;
}

void Logic::two_indexes_logic(int index0, int index1) {
	int num_common_unknown(0);
	for (int i : get_common_indexes(index0, index1)) {
		if (view_map[i] == 9) {
			++num_common_unknown;
		}
	}
	vector<int> suburb_indexes0(get_suburb_indexes(index0, index1));
	vector<int> suburb_indexes1(get_suburb_indexes(index1, index0));
	int num_unknown0(unknown_map[index0] - num_common_unknown);
	if (base_map[index0] - base_map[index1] == num_unknown0 + flags_map[index0] - flags_map[index1]) {
		for (int i : suburb_indexes0) {
			if (view_map[i] == 9) {
				cached_steps.push_back({i, 2});
			}
		}
		for (int i : suburb_indexes1) {
			if (view_map[i] == 9) {
				cached_steps.push_back({i, 0});
			}
		}
	}
}

void Logic::infer_single_box(int index) {
	if (!is_valuable(index)) {
		return;
	}
	if (flags_map[index] == base_map[index]) {
		cached_steps.push_back({index, 1});
	}
	if (unknown_map[index] + flags_map[index] == base_map[index]) {
		for (int i : surrounding_indexes[index]) {
			if (view_map[i] == 9) {
				cached_steps.push_back({i, 2});
			}
		}
	}
	vector<int> exp_indexes(sub_surrounding_indexes[index]);
	for (int exp_index : exp_indexes) {
		if (is_valuable(exp_index)) {
			two_indexes_logic(index, exp_index);
		}
	}
}

const step_t Logic::make_random_choice() {
	vector<int> blank_indexes;
	for (int i = 0; i < num_boxes; ++i) {
		if (view_map[i] == 9) {
			blank_indexes.push_back(i);
		}
	}
	int random_index(random_choice(blank_indexes));
	previous_index = random_index;
	step_t random_step {random_index, 3};
	return random_step;
}

const step_t Logic::make_choice() {
	auto iter = cached_steps.cbegin();
	while (iter != cached_steps.cend()) {
		if (view_map[iter->first] != 9) {
			iter = cached_steps.erase(iter);
		} else {
			++iter;
		}
	}
	if (!cached_steps.empty()) {
		step_t result(cached_steps.front());
		cached_steps.pop_front();
		return result;
	}
	set_spiral_trace_generator(previous_index);
	for (int _ = 0; _ < num_boxes; ++_) {
		infer_single_box(next_index);
		if (!cached_steps.empty()) {
			unlock_spiral_trace_generator();
			previous_index = next_index;
			step_t result(cached_steps.front());
			cached_steps.pop_front();
			return result;
		}
		move_to_next_index();
	}
	unlock_spiral_trace_generator();
	step_t random_step(make_random_choice());
	return random_step;
}

const int Logic::make_first_choice_index() {
	int first_index(coord_to_index({map_width / 2, map_height / 2}));
	previous_index = first_index;
	return first_index;
}

void Logic::on_playing() {
	int first_index(make_first_choice_index());
	start(first_index);
	step_t first_step({first_index, 0});
	exploit_step(first_step);
	while (game_status == 1) {
		step_t next_step(make_choice());
		exploit_step(next_step);
	}
}


const vector<pair<string, int>> Interface::BOX_CHAR_LIST({
	{"\u3000", 0x00},  // black        "　"
	{"\uff11", 0x03},  // dark skyblue "１"
	{"\uff12", 0x0a},  // green        "２"
	{"\uff13", 0x0c},  // red          "３"
	{"\uff14", 0x05},  // dark pink    "４"
	{"\uff15", 0x04},  // dark red     "５"
	{"\uff16", 0x0b},  // skyblue      "６"
	{"\uff17", 0x07},  // dark white   "７"
	{"\uff18", 0x08},  // dark gray    "８"
	{"\u2588", 0x7f},  // white        "█"
	{"\u25cf", 0x7d},  // pink         "●"
	{"\uff0a", 0x7c},  // red          "＊"
	{"\u203b", 0x76},  // dark yellow  "※"
	{"\u2573", 0x08},  // dark gray    "╳"
	// enclosed_box: black
	// revealed_box: dark white
});
const vector<pair<string, int>> Interface::GAME_STATUS_LIST({
	{"Preparing...", 0x0e},   // yellow
	{"Processing...", 0x0e},  // yellow
	{"Game won!", 0x0a},      // green
	{"Game over!", 0x0c},     // red
});
const vector<string> Interface::GAME_BASE_INFO_KEYS({
	"Size", "Progress", "Mines", "Steps", "Guesses"
});
const string Interface::CELL_SEPARATOR("  ");
const vector<vector<string>> Interface::FRAME_PARTS({
	{"\u250f", "\u2501", "\u2513"},  // ┏━┓
	{"\u2503", "\u2588", "\u2503"},  // ┃█┃
	{"\u2517", "\u2501", "\u251b"},  // ┗━┛
});
const string Interface::FINISH_MSG("Finished!");
const string Interface::INIT_FAILURE_MSG("Fatal: Failed to form a mine map with so many mines!");

Interface::Interface(int mw, int mh, int nm, int dm, int rm, double spsid):
	Logic(mw, mh, nm),
	display_mode(dm),
	record_mode(rm),
	sleep_per_step_if_displayed(spsid),
	display_map(dm == 0 || dm == 1),

	step_index_list(vector<int>()),
	step_mode_list(vector<int>()),

	status_info_width(0),
	cell_width(0),
	console_cols(0),
	console_lines(0)
{
	init_interface_params();
}

void Interface::init_interface_params() {
	int base_info_cell_num(static_cast<int>(GAME_BASE_INFO_KEYS.size()));
	vector<string> longest_base_info_values(get_game_base_info_values_template(
		0, num_mines, num_boxes, num_boxes
	));
	assert(base_info_cell_num == longest_base_info_values.size());
	for (const pair<string, int> &val : GAME_STATUS_LIST) {
		status_info_width = max(status_info_width, static_cast<int>(val.first.size()));
	}
	for (const string &val : GAME_BASE_INFO_KEYS) {
		cell_width = max(cell_width, static_cast<int>(val.size()));
	}
	for (const string &val : longest_base_info_values) {
		cell_width = max(cell_width, static_cast<int>(val.size()));
	}
	int cell_ceparator_length(static_cast<int>(CELL_SEPARATOR.size()));
	int base_info_width((cell_width + cell_ceparator_length) * base_info_cell_num - cell_ceparator_length);
	int cols(max(static_cast<int>(COPYRIGHT_STR.size()), base_info_width));
	int lines;
	switch (display_mode) {
		case 3: {
			lines = 3;
			break;
		}
		case 2: {
			lines = 6;
			break;
		}
		default: {
			cols = max(cols, (map_width + 2) * 2);
			lines = map_height + 8;
		}
	}
	console_cols = cols;
	console_lines = lines;
}

const vector<string> Interface::get_game_base_info_values_template(int nub, int num, int ns, int nrs) const {
	return {
		to_string(map_width) + " * " + to_string(map_height),
		to_string(num_boxes - nub) + " / " + to_string(num_boxes),
		to_string(num) + " / " + to_string(num_mines),
		to_string(ns),
		to_string(nrs),
	};
}

void Interface::re_initialize() {
	Logic::re_initialize();
	step_index_list.clear();
	step_mode_list.clear();
}

void Interface::exploit_step(const step_t &step) {
	if (record_mode != 0) {
		step_index_list.push_back(step.first);
		step_mode_list.push_back(step.second);
	}
	Logic::exploit_step(step);
	if (display_map) {
		if (display_mode == 0) {
			print_game_base_info_values();
		}
		if (game_status == 1) {
			Sleep((int)(sleep_per_step_if_displayed * 1000));
		}
	}
}

void Interface::start(int first_index) {
	Logic::start(first_index);
	if (display_mode == 0) {
		print_game_status();
	}
}

void Interface::end() {
	if (display_mode == 3) {
		return;
	}
	print_game_status();
	if (display_mode != 0) {
		print_game_base_info_values();
	}
}

void Interface::explode(const vector<int> &indexes) {
	Logic::explode(indexes);
	end();
}

void Interface::win() {
	Logic::win();
	end();
}

const COORD_T Interface::calculate_console_coord(int index) const {
	COORD_T coord(index_to_coord(index));
	return {(coord.first + 1) * 2, coord.second + 5};
}

void Interface::update_map(int index) const {
	if (!display_map) {
		return;
	}
	pair<string, int> box_char_pair(BOX_CHAR_LIST[view_map[index]]);
	COORD_T console_coord(calculate_console_coord(index));
	CONSOLE.print_at(console_coord, box_char_pair.first, box_char_pair.second);
}

void Interface::print_game_status() {
	pair<string, int> status_pair(GAME_STATUS_LIST[game_status]);
	CONSOLE.print_in_line(
		1, set_space(status_pair.first, status_info_width, -1), status_pair.second
	);
}

const vector<string> Interface::get_game_base_info_values() const {
	return get_game_base_info_values_template(
		num_unknown_boxes, num_unknown_mines,
		num_steps, num_random_steps
	);
}

void Interface::print_game_base_info_keys() {
	CONSOLE.print_list_as_table_row(
		2, GAME_BASE_INFO_KEYS, cell_width, 1, CELL_SEPARATOR
	);
}

void Interface::print_game_base_info_values() {
	CONSOLE.print_list_as_table_row(
		3, get_game_base_info_values(), cell_width, 1, CELL_SEPARATOR
	);
}

void Interface::init_display_frame() {
	int right_side_index(2 * (map_width + 1));
	CONSOLE.print_in_line(4, FRAME_PARTS[0][0] + repeat_str(map_width, FRAME_PARTS[0][1]) + FRAME_PARTS[0][2]);
	for (int line_index = 5; line_index < map_height + 5; ++line_index) {
		CONSOLE.print_in_line(line_index, FRAME_PARTS[1][0]);
	}
	for (int line_index = 5; line_index < map_height + 5; ++line_index) {
		CONSOLE.print_at({right_side_index, line_index}, FRAME_PARTS[1][2]);
	}
	CONSOLE.print_in_line(map_height + 5, FRAME_PARTS[2][0] + repeat_str(map_width, FRAME_PARTS[2][1]) + FRAME_PARTS[2][2]);
}

void Interface::display_new_view_map() {
	pair<string, int> blank_pair(BOX_CHAR_LIST[9]);
	int blank_color(blank_pair.second);
	string view_map_line_str(repeat_str(map_width, blank_pair.first));
	for (int line_index = 5; line_index < map_height + 5; ++line_index) {
		CONSOLE.print_at({2, line_index}, view_map_line_str, blank_color);
	}
}

void Interface::prepare_console(int cols, int lines) {
	CONSOLE.clear_console();
	CONSOLE.hide_cursor();
	CONSOLE.set_console_size(cols, lines);
	CONSOLE.print_copyright_str();
	if (display_mode != 3) {
		print_game_base_info_keys();
		print_game_base_info_values();
		if (display_map) {
			init_display_frame();
		}
	}
}

void Interface::begin_process() {
	prepare_console(console_cols, console_lines);
}

void Interface::run() {
	if (display_map) {
		if (display_mode == 0) {
			print_game_base_info_values();
		}
		display_new_view_map();
	}
	Logic::run();
}

void Interface::terminate_process() {
	CONSOLE.print_at_end(1, FINISH_MSG, 0x0a);
	CONSOLE.ready_to_quit();
}

void Interface::raise_init_mine_map_error() {
	CONSOLE.print_at_end(1, INIT_FAILURE_MSG, 0x0c);
	CONSOLE.ready_to_quit();
}


int main()
{
	Interface game(30, 16, 99, 0, 0, 0.0);
	int test_times(10);
	int won_count(0);
	double time_sum(0.0);
	game.begin_process();
	for (int t = 0; t < test_times; ++t) {
		game.run();
		time_sum += game.time_used;
		game.re_initialize();
	}
	game.terminate_process();
	return 0;
}
