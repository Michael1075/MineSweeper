#include "cpp_autosweeper.h"


using namespace std;


Core::Core() = default;

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

	game_status(),
	num_steps(),
	num_random_steps(),
	previous_index(),
	time_used(),

	surrounding_indexes(vector<vector<int>>(num_boxes)),
	sub_surrounding_indexes(vector<vector<int>>(num_boxes)),

	trace_lock(false),
	layer(),
	x0(),
	y0(),
	dx(),
	dy(),
	next_coord(),
	next_index()
{
	init_surrounding_indexes();
}

Core::~Core() = default;

void Core::init_surrounding_indexes() {
	for (int i = 0; i < num_boxes; ++i) {
		surrounding_indexes[i] = get_surrounding_indexes(i);
		sub_surrounding_indexes[i] = get_surrounding_indexes(i, 2);
	}
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
	mine_indexes = random::random_choices(map_index_choices, num_mines);
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


Logic::Logic() = default;

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
	int random_index(random::random_choice(blank_indexes));
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
	if (cached_steps.size()) {
		step_t result(cached_steps.front());
		cached_steps.pop_front();
		return result;
	}
	set_spiral_trace_generator(previous_index);
	for (int _ = 0; _ < num_boxes; ++_) {
		infer_single_box(next_index);
		if (cached_steps.size()) {
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


const char *SingleGame::INIT_FAILURE_MSG("Fatal: Too many mines!");

SingleGame::SingleGame() = default;

SingleGame::SingleGame(int mw, int mh, int nm, int rm):
	Logic(mw, mh, nm),
	record_mode(rm),

	step_index_list(),
	step_mode_list()
{}

void SingleGame::exploit_step(const step_t &step) {
	if (record_mode != 0) {
		step_index_list.push_back(step.first);
		step_mode_list.push_back(step.second);
	}
	Logic::exploit_step(step);
}

void SingleGame::raise_init_mine_map_error() {
	CONSOLE.move_cursor_to_end_line(1);
	CONSOLE.printf_with_color(INIT_FAILURE_MSG, 0x0c);
	CONSOLE.ready_to_quit();
}


GameRecorder::GameRecorder() = default;

GameRecorder::GameRecorder(const SingleGame &game):
	map_width(game.map_width),
	map_height(game.map_height),
	num_mines(game.num_mines),
	game_status(game.game_status),
	progress(game.num_boxes - game.num_unknown_boxes),
	num_flags(game.num_mines - game.num_unknown_mines),
	num_steps(game.num_steps),
	num_guesses(game.num_random_steps),
	time_used(game.time_used),
	mine_indexes(game.mine_indexes),
	step_index_list(game.step_index_list),
	step_mode_list(game.step_mode_list),
	output_file()
{}

GameRecorder::~GameRecorder() = default;

void GameRecorder::add_item(const char *key, int value) {
	fprintf(output_file, "\"%s\": \"%d\",\n", key, value);
}

void GameRecorder::add_item(const char *key, const char *value) {
	fprintf(output_file, "\"%s\": \"%s\",\n", key, value);
}

void GameRecorder::add_grouped_item(const char *key, const vector<int> &ints) {
	fprintf(output_file, "\"%s\": \"", key);
	for (auto iter = ints.cbegin(), last_iter = ints.cend() - 1; iter != last_iter; ++iter) {
		fprintf(output_file, "%d ", *iter);
	}
	fprintf(output_file, "%d\",\n", ints.back());
}

void GameRecorder::add_joined_item(const char *key, const vector<int> &ints) {
	fprintf(output_file, "\"%s\": \"", key);
	for (auto iter = ints.cbegin(), last_iter = ints.cend(); iter != last_iter; ++iter) {
		fprintf(output_file, "%d", *iter);
	}
	fprintf(output_file, "\",\n");
}

void GameRecorder::write_file() {
	char time_used_str[64];
	sprintf(time_used_str, "%6f ms", time_used * 1e3);
	fprintf(output_file, "{\n");
	add_item("map_width", map_width);
	add_item("map_height", map_height);
	add_item("num_mines", num_mines);
	add_item("game_result", (game_status == 2 ? "won" : "lost"));
	add_item("progress", progress);
	add_item("num_flags", num_flags);
	add_item("num_steps", num_steps);
	add_item("num_guesses", num_guesses);
	add_item("time_used", time_used_str);
	add_grouped_item("mine_indexes", mine_indexes);
	add_grouped_item("step_indexes", step_index_list);
	add_joined_item("step_mode_nums", step_mode_list);
	fprintf(output_file, "}");
}

void GameRecorder::record(int game_file_index, const char *path) {
	char file_path[64];
	sprintf(file_path, "%s\\%d.json", path, game_file_index);
	assert(!os::exists(file_path));
	output_file = fopen(file_path, "w");
	write_file();
	fclose(output_file);
}


const char *Interface::FINISH_MSG("Finished!");
const char *Interface::FOLDER_NAME("game_savings");


Interface::Interface() = default;

Interface::Interface(int mw, int mh, int nm, int rm):
	map_width(mw),
	map_height(mh),
	num_mines(nm),
	num_boxes(mw * mh),
	record_mode(rm),

	game_file_index(-1),

	console_cols(static_cast<int>(strlen(COPYRIGHT_STR))),
	console_lines(3),
	folder_path()
{
	init_folder_path();
}

Interface::~Interface() = default;

void Interface::init_folder_path() {
	if (!os::exists(FOLDER_NAME)) {
		os::make_dir(FOLDER_NAME);
	}
	sprintf(folder_path, "%s\\%d-%d-%d", FOLDER_NAME, map_width, map_height, num_mines);
}

const int Interface::get_num_of_files() const {
	if (!os::exists(folder_path)) {
		os::make_dir(folder_path);
		return 0;
	}
	return os::count_num_files(folder_path);
}

const GameRecorder Interface::get_recorder(const SingleGame &game) const {
	return GameRecorder(game);
}

void Interface::record_game_using_recorder(GameRecorder &game_recorder) const {
	if (game_file_index == -1) {
		game_file_index = get_num_of_files();
	} else {
		++game_file_index;
	}
	game_recorder.record(game_file_index, folder_path);
}

void Interface::record_game_data(const SingleGame &game) const {
	GameRecorder game_recorder(get_recorder(game));
	record_game_using_recorder(game_recorder);
}

void Interface::judge_to_record_game_data(const SingleGame &game) const {
	if (record_mode == 1 || record_mode == 2 && game.game_status == 2 || record_mode == 3 && game.game_status == 3) {
		record_game_data(game);
	}
}

void Interface::prepare_console(int cols, int lines) const {
	CONSOLE.ready_to_begin(cols, lines);
	printf(COPYRIGHT_STR);
}

void Interface::begin_process() const {
	prepare_console(console_cols, console_lines);
}

void Interface::terminate_process() const {
	CONSOLE.move_cursor_to_end_line(1);
	CONSOLE.printf_with_color(FINISH_MSG, 0x0a);
	CONSOLE.ready_to_quit();
}


const char *GameStatistics::STATISTICS_TITLE("- Statistics -");
const vector<const char*> GameStatistics::STATISTICS_KEYS({
	"Specification", "Main progress", "Games won", "Without guesses",
	"Avg. progress", "Avg. flags", "Avg. steps", "Avg. steps (won)",
	"Avg. guesses", "Avg. time", "Avg. time (won)", "Total avg. time"
});
const int GameStatistics::KEY_VAL_SEPARATOR_WIDTH(1);

GameStatistics::GameStatistics() = default;

GameStatistics::GameStatistics(int mw, int mh, int nm, int ng, int rm, int uf):
	Interface(mw, mh, nm, rm),
	single_game(SingleGame(mw, mh, nm, rm)),
	num_games(ng),
	update_freq(uf),
	serial_num(),
	num_games_won(),
	num_games_won_without_guesses(),
	progress_sum(),
	num_flags_sum(),
	num_steps_sum(),
	num_won_games_steps_sum(),
	num_random_steps_sum(),
	time_sum(),
	won_games_time_sum(),
	process_begin_time(),
    game_end_time(),
	num_recorded_games(record_mode < 0 ? -record_mode : 0),
	ranking_list(),

	key_info_width(),
	value_info_width(),
	statistic_info_width()
{
	init_statistics_params();
}

void GameStatistics::init_statistics_params() {
	for (const char *key : STATISTICS_KEYS) {
		key_info_width = max(key_info_width, static_cast<int>(strlen(key)));
	}
	char arr[6][64];
	double max_time(1e1);
	sprintf(arr[0], "%d * %d / %d (%.2f%%)", map_width, map_height, num_mines, f_div(num_mines, num_boxes) * 1e2);
	sprintf(arr[1], "%d / %d (%.2f%%)", num_games, num_games, 1e2);
	sprintf(arr[2], "%.3f / %d (%.2f%%)", static_cast<double>(num_boxes), num_boxes, 1e2);
	sprintf(arr[3], "%.3f / %d (%.2f%%)", static_cast<double>(num_mines), num_mines, 1e2);
	sprintf(arr[4], "%.3f step(s)", static_cast<double>(num_boxes));
	sprintf(arr[5], "%.6f ms", max_time * 1e3);
	for (int i = 0; i < 6; ++i) {
		value_info_width = max(value_info_width, static_cast<int>(strlen(arr[i])));
	}
	statistic_info_width = key_info_width + KEY_VAL_SEPARATOR_WIDTH + value_info_width;
	assert(static_cast<int>(strlen(STATISTICS_TITLE)) <= statistic_info_width);
	console_cols = max(console_cols, statistic_info_width);
	console_lines += static_cast<int>(STATISTICS_KEYS.size()) + 1;
}

void GameStatistics::print_statistics_keys() const {
	CONSOLE.move_cursor_to({(statistic_info_width - static_cast<int>(strlen(STATISTICS_TITLE))) / 2, 1});
	printf("%s\n", STATISTICS_TITLE);
	for (const char *key : STATISTICS_KEYS) {
		printf("%s\n", key);
	}
}

void GameStatistics::print_statistics_values() const {
	double avg_progress(f_div(progress_sum, serial_num));
	double avg_num_flags(f_div(num_flags_sum, serial_num));
	double avg_num_steps(f_div(num_steps_sum, serial_num));
	double avg_won_games_num_steps(f_div(num_won_games_steps_sum, num_games_won));
	double avg_num_random_steps(f_div(num_random_steps_sum, serial_num));
	double avg_time(f_div(time_sum, serial_num));
	double avg_won_games_time(f_div(won_games_time_sum, num_games_won));
	double total_avg_time(f_div(game_end_time - process_begin_time, serial_num));

	char arr[12][64];
	sprintf(arr[0], "%d * %d / %d (%.2f%%)", map_width, map_height, num_mines, f_div(num_mines, num_boxes) * 1e2);
	sprintf(arr[1], "%d / %d (%.2f%%)", serial_num, num_games, f_div(serial_num, num_games) * 1e2);
	sprintf(arr[2], "%d / %d (%.2f%%)", num_games_won, serial_num, f_div(num_games_won, serial_num) * 1e2);
	sprintf(arr[3], "%d / %d (%.2f%%)", num_games_won_without_guesses, serial_num, f_div(num_games_won_without_guesses, serial_num) * 1e2);
	sprintf(arr[4], "%.3f / %d (%.2f%%)", avg_progress, num_boxes, f_div(avg_progress, num_boxes) * 1e2);
	sprintf(arr[5], "%.3f / %d (%.2f%%)", avg_num_flags, num_mines, f_div(avg_num_flags, num_mines) * 1e2);
	sprintf(arr[6], "%.3f step(s)", avg_num_steps);
	sprintf(arr[7], "%.3f step(s)", avg_won_games_num_steps);
	sprintf(arr[8], "%.3f step(s)", avg_num_random_steps);
	sprintf(arr[9], "%.6f ms", avg_time * 1e3);
	sprintf(arr[10], "%.6f ms", avg_won_games_time * 1e3);
	sprintf(arr[11], "%.6f ms", total_avg_time * 1e3);

	int begin_col_index(key_info_width + KEY_VAL_SEPARATOR_WIDTH);
	for (int i = 0; i < 12; ++i) {
		CONSOLE.move_cursor_to({begin_col_index, i + 2});
		printf("%*s", value_info_width, arr[i]);
	}
}

void GameStatistics::update_statistics_data(const SingleGame &game) {
	if (game.game_status == 2) {
		++num_games_won;
		if (game.num_random_steps == 0) {
			++num_games_won_without_guesses;
		}
		num_won_games_steps_sum += game.num_steps;
		won_games_time_sum += game.time_used;
	}
	progress_sum += game.num_boxes - game.num_unknown_boxes;
	num_flags_sum += game.num_mines - game.num_unknown_mines;
	num_steps_sum += game.num_steps;
	num_random_steps_sum += game.num_random_steps;
	time_sum += game.time_used;
}

void GameStatistics::update_ranking_list(const SingleGame &game) {
	if (num_recorded_games == 0) {
		return;
	}
	GameRecorder game_recorder(get_recorder(game));
	if (game.num_unknown_boxes == 0) {
		record_game_using_recorder(game_recorder);
		--num_recorded_games;
	} else {
		int insert_index(static_cast<int>(ranking_list.size()));
		auto r_iter = ranking_list.crbegin(), r_last_iter = ranking_list.crend();
		while (r_iter != r_last_iter && r_iter->first >= game.num_unknown_boxes) {
			++r_iter;
		}
		ranking_list.insert(r_iter.base(), {game.num_unknown_boxes, game_recorder});
	}
	if (ranking_list.size() > num_recorded_games) {
		ranking_list.pop_back();
	}
}

void GameStatistics::begin_process() const {
	Interface::begin_process();
	print_statistics_keys();
	print_statistics_values();
}

void GameStatistics::run_single_game(SingleGame &game) {
	game = single_game;
	game.run();
	if (record_mode > 0) {
		judge_to_record_game_data(game);
	} else if (record_mode < 0) {
		update_ranking_list(game);
	}
	game_end_time = get_current_time();
	update_statistics_data(game);
}

void GameStatistics::run_all_games() {
	SingleGame game;
	while (serial_num < num_games) {
		run_single_game(game);
		++serial_num;
		if (serial_num % update_freq == 0 || serial_num == num_games) {
			print_statistics_values();
		}
	}
}

void GameStatistics::run_whole_process() {
	begin_process();
	srand((unsigned)time(NULL));
    process_begin_time = get_current_time();
	run_all_games();
	for (pair<int, GameRecorder> &pair_obj : ranking_list) {
		record_game_using_recorder(pair_obj.second);
	}
	terminate_process();
}


void cpp_main(int mw, int mh, int nm, int ng, int rm, int uf) {
	GameStatistics process(mw, mh, nm, ng, rm, uf);
	process.run_whole_process();
}


int main(int argc, char const *argv[]) {
	if (argc != 1 && (argc < 4 || argc > 7)) {
		printf("Please type in 0 or 3-6 attributes.\n");
		CONSOLE.pause();
		printf("\n");
		return 0;
	}
	int mw, mh, nm, ng, rm, uf;
	if (argc > 3) {
		mw = atoi(argv[1]);
		mh = atoi(argv[2]);
		nm = atoi(argv[3]);
	} else {
		mw = 30;
		mh = 16;
		nm = 99;
	}
	if (argc > 4) {
		ng = atoi(argv[4]);
	} else {
		ng = 1000;
	}
	if (argc > 5) {
		rm = atoi(argv[5]);
	} else {
		rm = 0;
	}
	if (argc > 6) {
		uf = atoi(argv[6]);
	} else {
		uf = ng / 100;
		if (uf == 0) {
			uf = 1;
		}
	}
	cpp_main(mw, mh, nm, ng, rm, uf);
	return 0;
}
