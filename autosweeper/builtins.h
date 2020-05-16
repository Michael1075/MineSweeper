#include <algorithm>
#include <iostream>
#include <map>
#include <regex>
#include <string>
#include <vector>

#ifndef _BUILTINS_H
#define _BUILTINS_H


using namespace std;


void raise(string error) {
	cout << error << endl;
	std::exit(1);
};

// shedskin

// const
// Check if some functions could be inherited from ARRAY_LIKE
// EVERYTHING, INCLUDING FUNCTION NAMES, FOLLOWS PYTHON.

struct ARRAY_LIKE {
public:
	void init_self(auto obj);

	void operator= (auto obj);
	void operator+= (auto obj);
	auto operator+ (auto obj);
	bool operator== (auto obj);
	bool operator!= (auto obj);
	auto operator[] (int index);

	auto begin();
	auto end();
	auto cbegin();
	auto cend();

	auto get_element(int index);
	auto slice(int start, int stop, int step);
	auto slice(int start, int stop);
	auto slice(int start);
	void convert_index(int index);
	int len();
	bool has_element();

	void append(auto sub_obj);
	void extend(auto obj);
	void insert(int index, auto sub_obj);
	int count(auto sub_obj);
	bool contains(auto sub_obj);
	int find_index(int index);
	auto get_reverse();
	void reverse();
	auto pop();
	auto pop(int index);
	void clear();

	auto copy();
};


struct STR: public ARRAY_LIKE {
public:
	string _str = "";
	typedef typename string::iterator iterator;
	typedef typename string::const_iterator const_iterator;

	// ::Initializers
	STR() {};

	STR(string string_obj) {
		this->_str = string_obj;
	};

	void init_self(STR str_obj) {
		this->init_string(str_obj._str);
	};

	void init_string(string string_obj) {
		this->_str = string_obj;
	};

	void init_char(char character) {
		string char_str (1, character);
		this->_str = char_str;
	};

	void init_int(int num) {
		this->_str = to_string(num);
	};

	void init_double(double double_num) {
		// int fix=16
		// this->_str = ... TODO
	};

	// ::ListFunctions
	void operator= (STR str_obj) {
		this->init_self(str_obj);
	};

	void operator+= (STR str_obj) {
		this->extend(str_obj);
	};

	STR operator+ (STR str_obj) const {
		STR result = this->copy();
		result.extend(str_obj);
		return result;
	};

	bool operator== (STR str_obj) const {
		return this->_str == str_obj._str;
	};

	bool operator!= (STR str_obj) const {
		return this->_str != str_obj._str;
	};

	STR operator[] (int index) const {
		return this->get_element(index);
	};

	iterator begin() {
		return this->_str.begin();
	};

	iterator end() {
		return this->_str.end();
	};

	const_iterator cbegin() const {
		return this->_str.cbegin();
	};

	const_iterator cend() const {
		return this->_str.cend();
	};

	STR get_element(int index) const {
		STR result;
		int abs_index = this->convert_index(index);
		if (abs_index == -1 || abs_index == this->len()) {
			raise("IndexError");
		};
		result.init_char((char)(this->_str[abs_index]));
		return result;
	};

	STR slice(int start, int stop, int step) const {
		STR result;
		int begin_index = this->convert_index(start);
		int end_index = this->convert_index(stop);
		if (step == 0) {
			raise("ValueError");
		} else if (step > 0) {
			for (int i = begin_index; i < end_index; i += step) {
				if (i != -1 && i != this->len()) {
					result.extend(this->get_element(i));
				};
			};
		} else {
			for (int i = begin_index; i > end_index; i += step) {
				if (i != -1 && i != this->len()) {
					result.extend(this->get_element(i));
				};
			};
		};
		return result;
	};

	STR slice(int start, int stop) const {
		STR result;
		int begin_index = this->convert_index(start);
		int end_index = this->convert_index(stop);
		int result_len = end_index - begin_index;
		if (result_len <= 0) {
			result.init_string("");
		} else {
			result.init_string(this->_str.substr(begin_index, result_len));
		};
		return result;
	};

	STR slice(int start) const {
		return this->slice(start, this->len());
	};

	int convert_index(int index) const {
		const int length = this->len();
		if (index < 0) {
			index += length;
		};
		if (index < 0) {
			return -1;
		};
		if (index >= length) {
			return length;
		};
		return index;
	};

	int len() const {
		return this->_str.size();
	};

	bool has_element() const {
		return bool(this->len());
	};

	void append(STR sub_str) {
		raise("NotImplementedError");
	};

	void extend(STR str_obj) {
		this->_str += str_obj._str;
	};

	void insert(int index, STR sub_str) {
		this->_str.insert(index, sub_str._str);
	};

	int count(STR sub_str) const {
		raise("NotImplementedError");
	};

	bool contains(STR sub_str) const {
		regex pattern (sub_str._str);
		return regex_search(this->_str, pattern);
	};

	int find_index(STR sub_str) const {
		// Return -1 if not found.
		return this->_str.find(sub_str._str);
	};

	STR get_reverse() const {
		STR result;
		for (int i = this->len() - 1; i >= 0; --i) {
			result.extend(this->get_element(i));
		};
		return result;
	};

	void reverse() {
		STR container = this->get_reverse();
		this->init_self(container);
	};

	STR pop() {
		STR result = this->get_element(-1);
		this->_str.pop_back();
		return result;
	};

	STR pop(int index) {
		STR result = this->get_element(index);
		this->_str.erase(this->begin() + index);
		return result;
	};

	void clear() {
		this->_str = "";
	};

	STR copy() const {
		STR result;
		result.init_string(this->_str);
		return result;
	};

	// ::OtherFunctions
	STR replace(STR sub_str, STR replacement_str) const {
		STR result;
		regex pattern (sub_str._str);
		result.init_string(regex_replace(this->_str, pattern, replacement_str._str));
		return result;
	};

	bool startswith(STR sub_str) const {
		return this->slice(0, sub_str.len()) == sub_str;
	};

	bool endswith(STR sub_str) const {
		return this->slice(-sub_str.len()) == sub_str;
	};

	STR format() const {
		//TODO
	};
};


template <typename T>
STR to_str(T obj) {
	cout << typeid(T).name() << endl;
	raise("NotImplementedError");
};

template <>
STR to_str(string string_obj) {
	return STR(string_obj);
};

template <>
STR to_str(char character) {
	STR result;
	result.init_char(character);
	return result;
};

template <>
STR to_str(int num) {
	STR result;
	result.init_int(num);
	return result;
};

template <>
STR to_str(double double_num) {
	STR result;
	result.init_double(double_num);
	return result;
};

template <>
STR to_str(STR p_str_obj) {
	return p_str_obj;
};


STR str(string string_obj) {
	return to_str<string>(string_obj);
};

STR str(const STR& str_obj) {
	return to_str<STR>(str_obj);
};

STR str(char character) {
	return to_str<char>(character);
};

STR str(int num) {
	return to_str<int>(num);
};

STR str(double double_num) {
	return to_str<double>(double_num);
};

STR str(const char* p_char) {
	return to_str<string>((string)p_char);
};


template <typename T>
struct LIST: public ARRAY_LIKE {
public:
	//friend ostream& operator<< <T>(ostream& cout, LIST& obj);

	vector<T> _vec;
	typedef typename vector<T>::iterator iterator;
	typedef typename vector<T>::const_iterator const_iterator;

	// ::Initializers
	LIST() {};

	//~LIST(); // TODO

	LIST(vector<T> vec_obj) {
		for (T i: vec_obj) {
			this->append(i);
		};
	};

	LIST(vector<string> vec_string_obj) {
		raise("NotImplementedError");
	};

	void init_self(LIST<T> list_obj) {
		this->init_vec(list_obj._vec);
	};

	void init_vec(vector<T> vec_obj) {
		this->clear();
		for (T i: vec_obj) {
			this->append(i);
		};
	};

	void init_size(int size, T element) {
		this->clear();
		for (int i = 0; i < size; ++i) {
			this->append(element);
		};
	};

	// ::ListFunctions
	void operator= (LIST<T> list_obj) {
		this->init_self(list_obj);
	};

	void operator+= (LIST<T> list_obj) {
		this->extend(list_obj);
	};

	LIST<T> operator+ (LIST<T> list_obj) const {
		LIST<T> result (this->_vec);
		result.extend(list_obj);
		return result;
	};

	bool operator== (LIST<T> list_obj) const {
		return this->_vec == list_obj._vec;
	};

	bool operator!= (LIST<T> list_obj) const {
		return this->_vec != list_obj._vec;
	};

	T operator[] (int index) const {
		return this->get_element(index);
	};

	iterator begin() {
		return this->_vec.begin();
	};

	iterator end() {
		return this->_vec.end();
	};

	const_iterator cbegin() const {
		return this->_vec.cbegin();
	};

	const_iterator cend() const {
		return this->_vec.cend();
	};

	T get_element(int index) const {
		int abs_index = this->convert_index(index);
		if (abs_index == -1 || abs_index == this->len()) {
			raise("IndexError");
		};
		return this->_vec[abs_index];
	};

	LIST<T> slice(int start, int stop, int step) const {
		int begin_index = this->convert_index(start);
		int end_index = this->convert_index(stop);
		LIST<T> result;
		if (step == 0) {
			raise("ValueError");
		} else if (step > 0) {
			for (int i = begin_index; i < end_index; i += step) {
				if (i != -1 && i != this->len()) {
					result.append(this->get_element(i));
				};
			};
		} else {
			for (int i = begin_index; i > end_index; i += step) {
				if (i != -1 && i != this->len()) {
					result.append(this->get_element(i));
				};
			};
		};
		return result;
	};

	LIST<T> slice(int start, int stop) const {
		int begin_index = this->convert_index(start);
		int end_index = this->convert_index(stop);
		LIST<T> result;
		for (int i = begin_index; i < end_index; ++i) {
			if (i != -1 && i != this->len()) {
				result.append(this->get_element(i));
			};
		};
		return result;
	};

	LIST<T> slice(int start) const {
		return this->slice(start, this->len());
	};

	int convert_index(int index) const {
		const int length = this->len();
		if (index < 0) {
			index += length;
		};
		if (index < 0) {
			return -1;
		};
		if (index >= length) {
			return length;
		};
		return index;
	};

	int len() const {
		return this->_vec.size();
	};

	bool has_element() const {
		return bool(this->len());
	};

	void append(T element) {
		this->_vec.push_back(element);
	};

	void extend(LIST<T> list_obj) {
		for (int i: list_obj._vec) {
			this->append(i);
		};
	};

	void insert(int index, T element) {
		this->_vec.insert(this->_vec.begin() + index, element);
	};

	int count(T element) const {
		return std::count(this->cbegin(), this->cend(), element);
	};

	bool contains(T element) const {
		return this->find_index(element) != -1;
	};

	int find_index(T element) const {
		int result = std::find(this->cbegin(), this->cend(), element) - this->cbegin();
		if (result == this->len()) {
			return -1;
		};
		return result;
	};

	LIST<T> get_reverse() const {
		LIST<T> result;
		for (int i = this->len() - 1; i >= 0; --i) {
			result.append(this->get_element(i));
		};
		return result;
	};

	void reverse() {
		LIST<T> container = this->get_reverse();
		this->init_self(container);
	};

	int pop() {
		int result = this->get_element(-1);
		this->_vec.pop_back();
		return result;
	};

	int pop(int index) {
		int result = this->get_element(index);
		result = this->get_element(index);
		this->_vec.erase(this->begin() + index);
		return result;
	};

	void clear() {
		this->_vec.clear();
	};

	LIST<T> copy() const {
		return LIST<T>(this->_vec);
	};

	// ::OtherFunctions
	void add(T element) {
		if (!this->contains(element)) {
			this->append(element);
		};
	};

	void sort() {
		std::sort(this->begin(), this->end());
	};

	LIST<T> make_set() const {
		vector<T> container = this->_vec;
		iterator vector_iter;
		std::sort(container.begin(), container.end());
		vector_iter = std::unique(container.begin(), container.end());
		if (vector_iter != container.end()) {
			container.erase(vector_iter, container.end());
		};
		return LIST<T>(container);
	};

	void as_set() {
		// After called, the elements will become ordered.
		this->init_self(this->make_set());
	};

	LIST<T> set_intersection(LIST<T> list_obj) const {
		vector<T> container;
		LIST<T> self_list_obj (this->_vec);
		self_list_obj.as_set();
		list_obj.as_set();
		std::set_intersection(self_list_obj.begin(), self_list_obj.end(),
			list_obj.begin(), list_obj.end(), back_inserter(container));
		return LIST<T>(container);
	};

	LIST<T> set_union(LIST<T> list_obj) const {
		vector<T> container;
		LIST<T> self_list_obj (this->_vec);
		self_list_obj.as_set();
		list_obj.as_set();
		std::set_union(self_list_obj.begin(), self_list_obj.end(),
			list_obj.begin(), list_obj.end(), back_inserter(container));
		return LIST<T>(container);
	};

	LIST<T> set_difference(LIST<T> list_obj) const {
		vector<T> container;
		LIST<T> self_list_obj (this->_vec);
		self_list_obj.as_set();
		list_obj.as_set();
		std::set_difference(self_list_obj.begin(), self_list_obj.end(),
			list_obj.begin(), list_obj.end(), back_inserter(container));
		return LIST<T>(container);
	};

	LIST<T> operator& (LIST<T> list_obj) const {
		return this->set_intersection(list_obj);
	};

	LIST<T> operator| (LIST<T> list_obj) const {
		return this->set_union(list_obj);
	};

	LIST<T> operator- (LIST<T> list_obj) const {
		return this->set_difference(list_obj);
	};

	STR join(STR joiner_str) const {
		STR result;
		if (!this->has_element()) {
			return result;
		};
		for (T i: this->slice(0, -1)) {
			result += to_str<T>(i);
			result += joiner_str;
		};
		result += to_str<T>(this->get_element(-1));
		return result;
	};
};


typedef LIST<int> ARRAY;


ARRAY range(int start, int stop, int step) {
	ARRAY result;
	if (step == 0) {
		raise("ValueError");
	} else if (step > 0) {
		for (int i = start; i < stop; i += step) {
			result.append(i);
		};
	} else {
		for (int i = start; i > stop; i += step) {
			result.append(i);
		};
	};
	return result;
};

ARRAY range(int start, int stop) {
	ARRAY result;
	for (int i = start; i < stop; ++i) {
		result.append(i);
	};
	return result;
};

ARRAY range(int stop) {
	ARRAY result;
	for (int i = 0; i < stop; ++i) {
		result.append(i);
	};
	return result;
};


typedef LIST<STR> STR_ARRAY;

template <>
STR_ARRAY::LIST(vector<string> vec_string_obj) {
	for (string i: vec_string_obj) {
		this->append(str(i));
	};
};


template <typename K, typename V>
struct DICT: public ARRAY_LIKE {
public:
	//friend ostream& operator<< <T>(ostream& cout, LIST& obj);
	typedef std::pair<K, V> PAIR;

	map<K, V> _map;
	typedef typename map<K, V>::iterator iterator;
	typedef typename map<K, V>::const_iterator const_iterator;

	// ::Initializers
	DICT() {};

	//~DICT(); // TODO

	DICT(map<K, V> map_obj) {
		//for (T i: map_obj) {
		//	this->append(i);
		//};
	};

	DICT(vector<string> vec_string_obj) {
		//raise("NotImplementedError"); //TODO
	};

	void init_self(DICT<K, V> list_obj) {
		this->init_map(list_obj._vec);
	};

	void init_map(map<K, V> map_obj) {
		this->clear();
		for (T i: map_obj) {
			this->append(i); //
		};
	};

	// ::ListFunctions
	void operator= (DICT<K, V> dict_obj) {
		this->init_self(dict_obj);
	};

	void operator+= (DICT<K, V> dict_obj) {
		this->extend(dict_obj);
	};

	DICT<K, V> operator+ (DICT<K, V> dict_obj) const {
		DICT<K, V> result (this->_map);
		result.extend(dict_obj);
		return result;
	};

	bool operator== (DICT<K, V> dict_obj) const {
		return this->_map == dict_obj._map;
	};

	bool operator!= (DICT<K, V> dict_obj) const {
		return this->_map != dict_obj._map;
	};

	V operator[] (K key_obj) const {
		//return this->get_element(index);
	};

	iterator begin() {
		return this->_map.begin();
	};

	iterator end() {
		return this->_map.end();
	};

	const_iterator cbegin() const {
		return this->_map.cbegin();
	};

	const_iterator cend() const {
		return this->_map.cend();
	};

	PAIR get_element(int index) const {
		int abs_index = this->convert_index(index);
		if (abs_index == -1 || abs_index == this->len()) {
			raise("IndexError");
		};
		return this->_map[abs_index];
	};

	DICT<K, V> slice(int start, int stop, int step) const {
		int begin_index = this->convert_index(start);
		int end_index = this->convert_index(stop);
		DICT<K, V> result;
		if (step == 0) {
			raise("ValueError");
		} else if (step > 0) {
			for (int i = begin_index; i < end_index; i += step) {
				if (i != -1 && i != this->len()) {
					result.append(this->get_element(i));
				};
			};
		} else {
			for (int i = begin_index; i > end_index; i += step) {
				if (i != -1 && i != this->len()) {
					result.append(this->get_element(i));
				};
			};
		};
		return result;
	};

	DICT<K, V> slice(int start, int stop) const {
		int begin_index = this->convert_index(start);
		int end_index = this->convert_index(stop);
		DICT<K, V> result;
		for (int i = begin_index; i < end_index; ++i) {
			if (i != -1 && i != this->len()) {
				result.append(this->get_element(i));
			};
		};
		return result;
	};

	DICT<K, V> slice(int start) const {
		return this->slice(start, this->len());
	};

	int convert_index(int index) const {
		const int length = this->len();
		if (index < 0) {
			index += length;
		};
		if (index < 0) {
			return -1;
		};
		if (index >= length) {
			return length;
		};
		return index;
	};

	int len() const {
		return this->_map.size();
	};

	bool has_element() const {
		return bool(this->len());
	};

	void append(PAIR element) {
		this->_map.push_back(element);
	};

	void extend(DICT<K, V> dict_obj) {
		for (int i: dict_obj._map) {
			this->append(i);
		};
	};

	void insert(int index, PAIR element) {
		this->_map.insert(this->_map.begin() + index, element);
	};

	int count(K key_obj) const {
		raise("NotImplementedError");
	};

	bool contains(K key_obj) const {
		return this->find_index(key_obj) != -1;
	};

	int find_index(K key_obj) const {
		int result = std::find(this->cbegin(), this->cend(), element) - this->cbegin();
		if (result == this->len()) {
			return -1;
		};
		return result;
	};

	DICT<K, V> get_reverse() const {
		DICT<K, V> result;
		for (int i = this->len() - 1; i >= 0; --i) {
			result.append(this->get_element(i));
		};
		return result;
	};

	void reverse() {
		DICT<K, V> container = this->get_reverse();
		this->init_self(container);
	};

	int pop() {
		int result = this->get_element(-1);
		this->_map.pop_back();
		return result;
	};

	int pop(int index) {
		int result = this->get_element(index);
		result = this->get_element(index);
		this->_map.erase(this->begin() + index);
		return result;
	};

	void clear() {
		this->_map.clear();
	};

	DICT<K, V> copy() const {
		return DICT<K, V>(this->_map);
	};

	// ::OtherFunctions
	LIST<K> keys() const {

	};

	LIST<V> values() const {

	};

	LIST<PAIR> items() const {

	};

}; //TODO


template <typename T>
STR repr(T obj) {
	cout << typeid(T).name() << endl;
	raise("NotImplementedError");
};

template<>
STR repr(STR obj) {
	STR container = obj.replace(str("'"), str("\\'"));
	container = container.replace(str("\""), str("\\\""));
	return str("'") + container + str("'");
};

template<>
STR repr(ARRAY obj) {
	STR joiner_str = str(", ");
	STR container = obj.join(joiner_str);
	return str("[") + container + str("]");
};

template<>
STR repr(STR_ARRAY obj) {
	STR_ARRAY arr_container;
	for (STR i: obj._vec) {
		arr_container.append(repr<STR>(i));
	};
	STR container = arr_container.join(str(", "));
	return str("[") + container + str("]");
};


void print(int num, string end) {
	cout << num << end;
};

void print(bool boolean, string end) {
	if (boolean) {
		cout << "true" << end;
	} else {
		cout << "false" << end;
	};
};

void print(const char* p_char, string end) {
	cout << p_char << end;
};

void print(string string_obj, string end) {
	// Note, pure strings are printed without ''.
	cout << string_obj << end;
};

void print(STR str_obj, string end) {
	// Note, STRs are printed with ''.
	cout << repr<STR>(str_obj)._str << end;
};

void print(ARRAY arr_obj, string end) {
	cout << repr<ARRAY>(arr_obj)._str << end;
};

void print(STR_ARRAY str_arr_obj, string end) {
	cout << repr<STR_ARRAY>(str_arr_obj)._str << end;
};

void print(auto obj) {
	print(obj, "\n");
};


void _exp_code() {
	print("Hello World!");
	ARRAY arr0;
	arr0.init_size(5, 2);
	arr0.extend(range(9));
	//arr0.clear();
	print(arr0);
	ARRAY arr1;
	arr1 = arr0.slice(-6, 7);
	print(arr1);
	arr1.extend(range(-3, 9, 2));
	arr1.append(3);
	arr1.append(6);
	print(arr1);
	arr1.as_set();
	print(arr1);

	//vector<int> vec = {1,6,7,3};
	ARRAY arr2 ({1,6,7,3});
	//arr2.init_vec(vec);
	print(arr2);
	arr2.sort();
	arr2.add(6);
	print(arr2);
	ARRAY arr3;
	arr3 = arr0 & arr1;
	print(arr3);
	arr3 = arr0 | arr1;
	print(arr3);
	arr3 = arr0 - arr1;
	print(arr3);
	arr3.reverse();
	print(arr3);

	ARRAY arr_sum;
	arr_sum = arr0 + arr1 + arr2;
	print(arr_sum);
	print(arr_sum.slice(7, 16));
	print(arr_sum);
	print(arr_sum.slice(-1, 8));
	int i = arr_sum[5];
	print(i);
	print(arr_sum.count(2));
	print(arr_sum.find_index(3));
	STR str0;
	str0.init_string("qwe");
	print(str0);
	STR str1;
	str1 = str("rty");
	print(str1);
	print("---");
	print(str1.find_index(str("q")));
	print(str1.find_index(str("t")));
	print(str1.find_index(str("rt")));

	STR str2;
	str2 = str0;
	print(str2);
	//bool boolean = (str2 == str0);
	print(str2 == str0);
	STR str3 = str2;
	print(str3);
	STR str4 ("qwq");
	print(str4);
	STR str5;
	str5 = str4.replace(str("q"), str("a"));
	print(str5);
	str0 += str1;
	print(str0);
	STR str6 ("I'm qwq \".");
	print(str6.len());
	print(str6);
	//print(str0[7]);
	//print(str0[6]);
	print(str0[5]);
	print(str0[-2]);
	print(str0.slice(3, 5));
	print(str0.slice(0, -2));
	print(str0.len());
	STR str7 ("qwerty");
	print(str7.slice(4, 1, -1));
	str7.reverse();
	print(str7);
	//str2.print();

	vector<STR> vec_str_obj = {str("Hello"), str("world"), str("!")};
	STR_ARRAY str_arr0 (vec_str_obj);
	str_arr0.init_vec(vec_str_obj);
	print(str_arr0.slice(5, 7));
	print(str_arr0);
	STR_ARRAY str_arr1 ({"Hello", "world", "!"});
	//STR_ARRAY str_arr1 (vec_string_obj);
	print(str_arr1.slice(1));
};


#endif
