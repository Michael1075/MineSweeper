"use strict"

String.prototype.format = function() {
	let args = [].slice.call(arguments);
	return this.replace(/(\{\d+\})/g, function(a) {
		return args[+(a.substr(1, a.length - 2)) || 0];
	});
};

String.prototype.beginswith = function(string) {
	return this.substr(0, string.length) === string;
};

String.prototype.get_positive_int = function() {
	if (/^[1-9]\d*$/g.test(this)) {
		return Number(this)
	} else {
		return 0;
	};
};

Array.prototype.contains = function(val) {
	for (let i of this) {
		if (i === val) {
			return true;
		};
	};
	return false;
};

Array.prototype.remove = function(val) {
	let index = this.indexOf(val);
	if (index > -1) {
		this.splice(index, 1);
	};
};

Array.prototype.count = function(val) {
	let counting = 0;
	for (let i of this) {
		if (i === val) {
			counting++;
		};
	};
	return counting;
};

Array.prototype.push_as_set = function(val) {
	if (!this.contains(val)) {
		this.push(val);
	};
};

function $(id) {
	return document.getElementById(id);
};

function $$(name) {
	return document.getElementsByName(name);
};

function random_int(min, max) {
	let randint = Math.floor(Math.random() * (max - min)) + min;
	return randint;
};

window.oncontextmenu = function(event){
	event.preventDefault();
};

const box_char_dict = {
	num0: "",
	num1: "1",
	num2: "2",
	num3: "3",
	num4: "4",
	num5: "5",
	num6: "6",
	num7: "7",
	num8: "8",
	blank: "",
	flag: "@",
	exploded_mine: "x",
	rest_mine: "x",
	wrong_flag: "-",
};

function Game(map_width, map_height, num_mines) {
	this.timer_succession = undefined;
	this.game_status = "prepare";
	this.map_width = map_width;
	this.map_height = map_height;
	this.num_mines = num_mines;
	this.num_boxes = map_width * map_height;
	this.base_map = new Array(this.num_boxes);
	this.view_map = new Array(this.num_boxes);
	this.num_rest_mines = num_mines;

	this.coord_to_index = function(x, y) {
		return x * this.map_width + y;
	};
	
	this.index_to_coord = function(index) {
		let x = Math.floor(index / this.map_width);
		let y = index % this.map_width;
		return [x, y];
	};
	
	this.get_surrounding_indexes_with_self = function(index) {
		let coord = this.index_to_coord(index);
		let x = coord[0];
		let y = coord[1];
		let result = new Array();
		for (let i = x-1; i <= x+1; i++) {
			if (0 <= i && i < this.map_height) {
				for (let j = y-1; j <= y+1; j++) {
					if (0 <= j && j < this.map_width) {
						let res_index = this.coord_to_index(i, j);
						result.push(res_index);
					};
				};
			};
		};
		return result;
	};
	
	this.get_surrounding_indexes = function(index) {
		let result = this.get_surrounding_indexes_with_self(index);
		result.remove(index);
		return result;
	};
	
	this.init_view_map = function() {
		for (let i = 0; i < this.num_boxes; i++) {
			this.view_map[i] = "blank";
		};
	};
	
	this.init_base_map = function(first_index) {
		let safe_region_indexes = this.get_surrounding_indexes_with_self(first_index);
		let map_index_choices = new Array();
		for (let i = 0; i < this.num_boxes; i++) {
			map_index_choices.push(i);
		};
		for (let i of safe_region_indexes) {
			map_index_choices.remove(i);
		};
		if (map_index_choices.length < this.num_mines) {
			return 1;
		};
		let mine_indexes = new Array(this.num_mines);
		for (let i = 0; i < this.num_mines; i++) {
			let choice = map_index_choices.splice(random_int(0, map_index_choices.length), 1);
			mine_indexes.push(choice);
			this.base_map[choice] = -1;
		};
		for (let i = 0; i < this.num_boxes; i++) {
			if (this.base_map[i] != -1) {
				this.base_map[i] = 0;
			};
		};
		for (let index of mine_indexes) {
			for (let i of this.get_surrounding_indexes(index)) {
				if (this.base_map[i] != -1) {
					this.base_map[i]++;
				};
			};
		};
		return 0;
	};
	
	this.show_init_map = function() {
		let table_str = "";
		for (let i = 0; i < this.map_height; i++) {
			table_str += "<tr>";
			for (let j = 0; j < this.map_width; j++) {
				let index = this.coord_to_index(i, j);
				let box_str = '<td id="b{0}" onmouseup="stream.game.click_box({0})"></td>'.format(index);
				table_str += box_str;
			};
			table_str += "</tr>";
		};
		$("game_table").innerHTML = table_str;
		for (let i = 0; i < this.num_boxes; i++) {
			this.update_map(i);
		};
	};
	
	this.update_map = function(index) {
		let box_type = this.view_map[index];
		let box_char = box_char_dict[box_type];
		let box_obj = $("b" + index);
		let base_box_type;
		if (box_type.beginswith("num") || box_type === "wrong_flag") {
			base_box_type = "revealed_box";
		} else {
			base_box_type = "enclosed_box";
		};
		box_obj.setAttribute("class", base_box_type + " " + box_type);
		box_obj.innerHTML = box_char;
	};
	
	this.explore_single_safe_box = function(index) {
		if (this.view_map[index] === "blank") {
			this.view_map[index] = "num" + this.base_map[index];
			this.update_map(index);
		};
	};
	
	this.flag_blank_box = function(index) {
		this.view_map[index] = "flag";
		this.update_map(index);
	};
	
	this.undo_flag_blank_box = function(index) {
		this.view_map[index] = "blank";
		this.update_map(index);
	};
	
	this.expand_zero = function(index) {
		let pre_updated_zero_region = new Array();
		let zero_region = new Array();
		zero_region.push(index);
		while (pre_updated_zero_region.length != zero_region.length) {
			pre_updated_zero_region = zero_region;
			for (let i of pre_updated_zero_region) {
				for (let j of this.get_surrounding_indexes_with_self(i)) {
					if (this.base_map[j] === 0) {
						zero_region.push_as_set(j);
					};
				};
			};
		};
		let expand_region = new Array();
		for (let i of zero_region) {
			for (let j of this.get_surrounding_indexes_with_self(i)) {
				if (this.view_map[j] === "blank") {
					this.explore_single_safe_box(j);
				};
			};
		};
	};
	
	this.explore_blank_box = function(index) {
		switch (this.base_map[index]) {
			case -1:
				this.explode([index]);
				break;
			case 0:
				this.expand_zero(index);
				break;
			default:
				this.explore_single_safe_box(index);
				break;
		};
	};
	
	this.explore_surrounding = function(index) {
		let surrounding_indexes = this.get_surrounding_indexes(index)
		let surrounding_vals = new Array();
		for (let i of surrounding_indexes) {
			surrounding_vals.push(this.view_map[i]);
		};
		if (surrounding_vals.count("flag") === this.base_map[index]) {
			let surrounding_mine_indexes = new Array();
			for (let i of surrounding_indexes) {
				if (this.base_map[i] === -1 && this.view_map[i] != "flag") {
					surrounding_mine_indexes.push(i);
				};
			};
			if (surrounding_mine_indexes.length > 0) {
				this.explode(surrounding_mine_indexes);
			} else {
				for (let i of surrounding_indexes) {
					if (this.view_map[i] === "blank") {
						this.explore_blank_box(i);
					};
				};
			};
		};
	};

	this.left_click_box = function(index) {
		switch (this.game_status) {
			case "prepare":
				let map_generator = this.init_base_map(index);
				switch (map_generator) {
					case 0:
						this.game_status = "ongoing";
						this.start_timer();
						this.left_click_box(index);
						break;
					case 1:
						alert("Failed to form a mine map!\nYou may have to change settings.");
						break;
				};
				break;
			case "ongoing":
				switch (this.view_map[index]) {
					case "blank":
						this.explore_blank_box(index);
						break;
					case "flag":
						break;
					case "num0":
						break;
					default:
						this.explore_surrounding(index);
						break;
				};
				if (this.game_status === "ongoing") {
					this.check_if_win();
				};
				break;
			default:
				break;
		};
	};
	
	this.right_click_box = function(index) {
		switch (this.game_status) {
			case "ongoing":
				switch (this.view_map[index]) {
					case "blank":
						this.flag_blank_box(index);
						this.num_rest_mines--;
						this.update_num_rest_mines();
						break;
					case "flag":
						this.undo_flag_blank_box(index);
						this.num_rest_mines++;
						this.update_num_rest_mines();
						break;
					default:
						break;
				};
				break;
			default:
				break;
		};
	};

	this.mouse_down = function(index) {
		switch (event.button) {
			case 0:
				this.left_click_down_box(index);
				break;
		};
	};
	
	this.click_box = function(index) {
		switch (event.button) {
			case 0:
				this.left_click_box(index);
				break;
			case 2:
				this.right_click_box(index);
				break;
		};
	};
	
	this.explode = function(indexes) {
		for (let i of indexes) {
			this.view_map[i] = "exploded_mine";
			this.update_map(i);
		};
		for (let i = 0; i < this.num_boxes; i++) {
			if (this.base_map[i] === -1 && this.view_map[i] != "flag" && this.view_map[i] != "exploded_mine") {
				this.view_map[i] = "rest_mine";
				this.update_map(i);
			} else if (this.base_map[i] != -1 && this.view_map[i] === "flag") {
				this.view_map[i] = "wrong_flag";
				this.update_map(i);
			};
		};
		this.game_status = "game_over";
		this.stop_timer();
		this.show_game_status("T^T");
	};
	
	this.check_if_win = function() {
		if (this.view_map.count("blank") === this.num_rest_mines) {
			for (let i = 0; i < this.num_boxes; i++) {
				if (this.view_map[i] === "blank") {
					this.flag_blank_box(i);
				};
			};
			this.num_rest_mines = 0;
			this.update_num_rest_mines();
			this.game_status = "game_won";
			this.stop_timer();
			this.show_game_status("^v^");
		} else {
			this.show_game_status("-_-");
		};
	};
	
	this.update_num_rest_mines = function() {
		$("rest_mines_counter").innerHTML = this.num_rest_mines;
	};
	
	this.show_game_status = function(text) {
		$("game_status").innerHTML = text;
	};
	
	this.update_timer = function(elapsed_time) {
		let minutes = Math.floor(elapsed_time / 60);
		let seconds = this.modify_timer_str(Math.floor(elapsed_time % 60));
		let hseconds = this.modify_timer_str(Math.floor(elapsed_time * 100 % 100));
		let time_str = "{0}\'{1}\"{2}".format(minutes, seconds, hseconds);
		$("timer").innerHTML = time_str;
	};
	
	this.modify_timer_str = function(partial_timer_val) {
		let result = partial_timer_val.toString();
		if (result.length === 1) {
			return "0" + result;
		} else {
			return result;
		};
	};
	
	this.display_timer = function(begin_time) {
		let current_time = new Date().getTime();
		let elapsed_time = (current_time - begin_time) / 1000;
		this.update_timer(elapsed_time);
	};
	
	this.start_timer = function() {
		let begin_time = new Date().getTime();
		let timer_cmd = "stream.game.display_timer({0})".format(begin_time);
		this.timer_succession = window.setInterval(timer_cmd, 10);
	};
	
	this.stop_timer = function() {
		if (this.timer_succession != undefined) {
			window.clearInterval(this.timer_succession);
			this.timer_succession = undefined;
		};
	};
	
	this.reset_timer = function() {
		this.stop_timer();
		this.update_timer(0);
	};
	
	this.play = function() {
		this.init_view_map();
		this.show_init_map();
		this.update_num_rest_mines();
		this.show_game_status("-_-");
		this.reset_timer();
	};
	
	this.stop_game = function() {
		this.stop_timer();
	};
};

function Stream() {
	this.settings_open = false;
	this.game = new Game(9, 9, 10);
	this.game.play();

	this.new_game = function(new_map_width, new_map_height, new_num_mines) {
		this.game.stop_game();
		this.game = new Game(new_map_width, new_map_height, new_num_mines);
		this.game.play();
		this.click_settings();
	};
	
	this.click_confirm = function() {
		let radio_buttons = $$("choice");
		let choice;
		for (let i = 0; i < radio_buttons.length; i++){
			if (radio_buttons[i].checked) {
				choice = radio_buttons[i].value;
			};
		};
		switch (choice) {
			case "easy":
				this.new_game(9, 9, 10);
				break;
			case "medium":
				this.new_game(16, 16, 40);
				break;
			case "difficult":
				this.new_game(30, 16, 99);
				break;
			case "customize":
				let new_map_width = $$("new_map_width")[0].value.get_positive_int();
				let new_map_height = $$("new_map_height")[0].value.get_positive_int();
				let new_num_mines = $$("new_num_mines")[0].value.get_positive_int();
				if (new_map_width > 0 && new_map_height > 0 && new_num_mines > 0) {
					this.new_game(new_map_width, new_map_height, new_num_mines);
				} else {
					alert("You shall input 3 positive integers!");
				};
				break;
		};
	};
	
	this.click_settings = function() {
		let settings_obj_style = $("settings_grid").style;
		if (this.settings_open) {
			settings_obj_style.opacity = 0;
			setTimeout(function() {
				settings_obj_style.display = "none";
			}, 400)
		} else {
			settings_obj_style.display = "inline-grid";
			setTimeout(function() {
				settings_obj_style.opacity = 1;
			}, 20);
		};
		this.settings_open = !this.settings_open;
	};
};

var stream = new Stream();
