#ifndef _CPP_EXT_H
#define _CPP_EXT_H

#include "tools.h"
#include <iomanip>
#include <list>

#ifndef __author__
#define __author__ "Michael W"
#endif


using namespace std;
typedef pair<int, int> coord_t;
typedef pair<int, int> step_t;


struct Core;
struct Logic;
struct Interface;


struct Core: public RandomTools {
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

	Core(int mw, int mh, int nm);
	virtual ~Core();


	void init_surrounding_indexes();
	virtual void re_initialize();
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
	virtual void update_map(int index) const = 0;
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

	Logic(int mw, int mh, int nm);

	void init_unknown_map();
	virtual void re_initialize() override;
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


struct Interface: public Logic {
public:
	static const vector<pair<string, int>> BOX_CHAR_LIST;
	static const vector<pair<string, int>> GAME_STATUS_LIST;
	static const vector<string> GAME_BASE_INFO_KEYS;
	static const string CELL_SEPARATOR;
	static const vector<vector<string>> FRAME_PARTS;
	static const string FINISH_MSG;
	static const string INIT_FAILURE_MSG;

	int display_mode;
	int record_mode;
	double sleep_per_step_if_displayed;
	bool display_map;

	vector<int> step_index_list;
	vector<int> step_mode_list;

	int status_info_width;
	int cell_width;
	int console_cols;
	int console_lines;

	Interface(int mw, int mh, int nm, int dm, int rm, double spsid);

	void init_interface_params();
	const vector<string> get_game_base_info_values_template(int nub, int num, int ns, int nrs) const;
	void re_initialize() override;
	void exploit_step(const step_t &step) override;
	void start(int first_index) override;
	void end();
	void explode(const vector<int> &indexes) override;
	void win() override;
	const coord_t calculate_console_coord(int index) const;
	void update_map(int index) const override;
	void print_game_status();
	const vector<string> get_game_base_info_values() const;
	void print_game_base_info_keys();
	void print_game_base_info_values();
	void init_display_frame();
	void display_new_view_map();
	void prepare_console(int cols, int lines);
	void begin_process();
	void run() override;
	void terminate_process();
	void raise_init_mine_map_error() override;
};


#endif
