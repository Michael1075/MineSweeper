#ifndef _CPP_EXT_H
#define _CPP_EXT_H

#include "tools.h"
#include <cstring>
#include <iomanip>
#include <list>


using namespace std;


typedef pair<int, int> coord_t;
typedef pair<int, int> step_t;


struct Core;
struct Logic;
struct SingleGame;
struct GameRecorder;
struct Interface;
struct GameStatistics;


struct Core {
public:
	int map_width;
	int map_height;
	int num_mines;
	int num_boxes;
	int num_unknown_boxes;
	int num_unknown_mines;
	vector<int> mine_indexes;
	vector<int> base_map;
	vector<int> view_map;

	int game_status;
	int num_steps;
	int num_random_steps;
	int previous_index;
	double time_used;

	vector<vector<int>> surrounding_indexes;
	vector<vector<int>> sub_surrounding_indexes;

	bool trace_lock;
	int layer;
	int x0;
	int y0;
	int dx;
	int dy;
	coord_t next_coord;
	int next_index;

	Core();
	Core(int mw, int mh, int nm);
	virtual ~Core();

	void init_surrounding_indexes();

	const vector<int> get_union(const vector<int> &list0, const vector<int> &list1) const;
	const vector<int> get_difference(const vector<int> &list0, const vector<int> &list1) const;
	const int coord_to_index(const coord_t &coord) const;
	const coord_t index_to_coord(int index) const;
	const bool in_map(const coord_t &coord) const;

	void set_spiral_trace_generator(int center_index, int layer=-1);
	void move_to_next_index();
	void unlock_spiral_trace_generator();

	const vector<int> get_surrounding_indexes_with_self(int index, int layer=1);
	const vector<int> get_surrounding_indexes(int index, int layer=1);
	const vector<int> get_common_indexes(int index0, int index1) const;
	const vector<int> get_suburb_indexes(int index0, int index1) const;
	const vector<int> indexes_ordered_in_spiral(int index, vector<int> index_list);

	virtual void raise_init_mine_map_error() = 0;
	void init_mine_indexes(int first_index);
	void init_base_map();
	void reduce_num_unknown_boxes();
	void reduce_num_unknown_mines();
	void expand_zero(int index);
	virtual void explore_single_safe_box(int index);
	void explore_surrounding(int index);
	void explore_blank_box(int index);
	virtual void flag_blank_box(int index);
	virtual void exploit_step(const step_t &step);
	virtual void start(int first_index);
	virtual void explode(const vector<int> &indexes);
	virtual void win();
	void check_if_win();
	virtual void on_playing() = 0;
	virtual void run();
};


struct Logic: public Core {
public:
	vector<int> unknown_map;
	vector<int> flags_map;
	list<step_t> cached_steps;

	Logic();
	Logic(int mw, int mh, int nm);

	void init_unknown_map();

	void modify_surrounding_unknown_map(int index);
	void modify_surrounding_flags_map(int index);
	void explore_single_safe_box(int index) override;
	void flag_blank_box(int index) override;
	const bool is_valuable(int index) const;
	void two_indexes_logic(int index0, int index1);
	void infer_single_box(int index);
	const step_t make_random_choice();
	const step_t make_choice();
	const int make_first_choice_index();
	void on_playing() override;
};


struct SingleGame: public Logic {
public:
	static const char *INIT_FAILURE_MSG;

	int record_mode;

	vector<int> step_index_list;
	vector<int> step_mode_list;

	SingleGame();
	SingleGame(int mw, int mh, int nm, int rm);

	void exploit_step(const step_t &step) override;
	void raise_init_mine_map_error() override;
};


struct GameRecorder {
public:
	int map_width;
	int map_height;
	int num_mines;
	int game_status;
	int progress;
	int num_flags;
	int num_steps;
	int num_guesses;
	double time_used;
	vector<int> mine_indexes;
	vector<int> step_index_list;
	vector<int> step_mode_list;
	FILE *output_file;

	GameRecorder();
	GameRecorder(const SingleGame &game);
	virtual ~GameRecorder();

	void add_item(const char *key, int value);
	void add_item(const char *key, const char *value);
	void add_grouped_item(const char *key, const vector<int> &ints);
	void add_joined_item(const char *key, const vector<int> &ints);
	void write_file();
	void record(int game_file_index, const char *path);
};


struct Interface {
public:
	static const char *FINISH_MSG;
	static const char *FOLDER_NAME;

	int map_width;
	int map_height;
	int num_mines;
	int num_boxes;
	int record_mode;

	mutable int game_file_index;

	int console_cols;
	int console_lines;
	char folder_path[64];

	Interface();
	Interface(int mw, int mh, int nm, int rm);
	virtual ~Interface();

	void init_folder_path();

	const int get_num_of_files() const;
	const GameRecorder get_recorder(const SingleGame &game) const;
	void record_game_using_recorder(GameRecorder &game_recorder) const;
	void record_game_data(const SingleGame &game) const;
	void judge_to_record_game_data(const SingleGame &game) const;

	void prepare_console(int cols, int lines) const;
	virtual void begin_process() const;
	void terminate_process() const;
	const SingleGame get_single_game() const;
};


struct GameStatistics: public Interface {
public:
	static const char *STATISTICS_TITLE;
	static const vector<const char*> STATISTICS_KEYS;
	static const int KEY_VAL_SEPARATOR_WIDTH;

	int num_games;
	int update_freq;
	int num_games_won;
	int num_games_won_without_guesses;
	int progress_sum;
	int num_flags_sum;
	int num_steps_sum;
	int num_won_games_steps_sum;
	int num_random_steps_sum;
	double time_sum;
	double won_games_time_sum;
    double process_begin_time;
    double game_end_time;
	int num_recorded_games;
	list<pair<int, GameRecorder>> ranking_list;

	int key_info_width;
	int value_info_width;
	int statistic_info_width;

	GameStatistics();
	GameStatistics(int mw, int mh, int nm, int ng, int rm, int uf);

	void init_statistics_params();
	void print_statistics_keys() const;
	void print_statistics_values(int serial_num) const;
	void update_statistics_data(const SingleGame &game, int serial_num);
	void update_ranking_list(const SingleGame &game);
	void begin_process() const override;
	void run_whole_process();
};


void cpp_main(int mw, int mh, int nm, int ng, int rm, int uf);


#endif
