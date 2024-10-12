#include <fstream>
#include <random>
#include <sstream>
#include <stack>
#include <string>
#include <vector>
#include <windows.h>

#pragma comment(lib, "winmm.lib")   //编译时链接winmm.lib
#pragma once

class Note
    //以单音符形式播放指定声音
{
public:
    void open(void);
    void close(void);
    bool play_note(unsigned short note, unsigned short velocity, unsigned short instrument, unsigned short channel);
private:
    HMIDIOUT handle;
    bool test_input(unsigned short note, unsigned short velocity, unsigned short instrument, unsigned short channel);
};

void Note::open(void)
{
    midiOutOpen(&handle, 0, 0, 0, CALLBACK_NULL);
}

void Note::close(void)
{
    midiOutClose(handle);
}

bool Note::test_input(unsigned short note, unsigned short velocity, unsigned short instrument, unsigned short channel)
//判断输入是否合法
{
    if (note > 127) {
        return false;
    }
    if (velocity > 127) {
        return false;
    }
    if (instrument > 127) {
        return false;
    }
    if (channel > 15) {
        return false;
    }
    return true;
}

bool Note::play_note(unsigned short note, unsigned short velocity, unsigned short instrument = 0, unsigned short channel = 0)
//播放指定的声音,返回值为false时表示播放失败,没有其他错误原因返回
{
    if (Note::test_input(note, velocity, instrument, channel) == false) {
        return false;
    }

    //设置指定的乐器
    if (midiOutShortMsg(handle, 0xC0 + (instrument * 0x100)) != MMSYSERR_NOERROR) {
        return false;
    }
    //播放指定的声音
    if (midiOutShortMsg(handle, 0x90 + channel + (note * 0x100) + (velocity * 0x10000)) != MMSYSERR_NOERROR) {
        return false;
    }

    return true;
}

class Tracks
    //声明固定数量的音轨并进行管理
    // well, i agree that this class is useless. please do not use it.
{
public:
    Tracks();
    ~Tracks();
    void open(void);
    void close(void);
    void set_track(unsigned short track_num);
    void play(unsigned short (*play_set)[3]);
private:
    Note note;
    bool is_opened;
    unsigned short track_num;
};
Tracks::Tracks()
{
    is_opened = false;
    track_num = 1;
}
Tracks::~Tracks()
{
    Tracks::close();
}

//打开和关闭声卡的函数,不过和Note的版本相比,增加了状态判断的部分
void Tracks::open(void)
{
    if (is_opened) {
        return;
    }
    is_opened = true;
    note.open();
}
void Tracks::close(void)
{
    if (!is_opened) {
        return;
    }
    is_opened = false;
    note.close();
}

void Tracks::set_track(unsigned short number)
//设置音轨总数,不超过16条,如果意图设置16条以上会保留16条
{
    if (number > 16) {
        track_num = 16;
        return;
    }
    track_num = number;
}

void Tracks::play(unsigned short (*play_set)[3])
//为每个已声明的MIDI通道设置播放效果
//*play_set使用前track_num个
//play_set应该为[note, velocity, instrument]
{
    if (!is_opened) {
        return;
    }
    for (unsigned short channel = 0; channel < track_num; channel++) {
        note.play_note(**(play_set + channel), *(*(play_set + channel) + 1), *(*(play_set + channel) + 2), channel);
    }
}

class MarkovGenerater
    //生成基于Markov模型的随机输出.自动保存上次的状态
{
public:
    MarkovGenerater();
    void set_fixed_note(unsigned short note);
    void set_fixed_velocity(unsigned short velocity);
    void set_fixed_time(unsigned short time);
    void set_module_note(const char* filename);
    void set_module_velocity(const char* filename);
    void set_module_time(const char* filename);
    void set_seed(double seed);
    unsigned short play_note(Note midi_note, unsigned short instrument, unsigned short channel);
    void print_matrix(void);

private:
    bool set_velocity, set_note, set_time;
    unsigned short fixed_velocity, fixed_note, fixed_time;
    std::default_random_engine rnd_engine;
    std::uniform_real_distribution<double> rnd_;
    // 管理的数据
    // stk_是存储上次状态的栈
    // index_表示状态对应的实际值(通常是间断的)
    // vec1_是无上次状态时的概率分布
    // vec2_实际上是矩阵,存的是所有上次状态的条件概率分布
    // 音高
    std::stack<unsigned short> stk_note;
    std::vector<unsigned short> index_note;
    std::vector<double> vec1_note;
    std::vector<std::vector<double>> vec2_note;
    // 音量
    std::stack<unsigned short> stk_velocity;
    std::vector<unsigned short> index_velocity;
    std::vector<double> vec1_velocity;
    std::vector<std::vector<double>> vec2_velocity;
    // 时长
    std::stack<unsigned short> stk_time;
    std::vector<unsigned short> index_time;
    std::vector<double> vec1_time;
    std::vector<std::vector<double>> vec2_time;

    unsigned short rnd_get(std::vector<double> p_vec);
    void get_matrix(const char* filename, std::vector<unsigned short>& index, std::vector<double> &vec1, std::vector<std::vector<double>> &vec2);
    unsigned short get_value(std::stack<unsigned short> stk, std::vector<unsigned short>& index, std::vector<double>& vec1, std::vector<std::vector<double>>& vec2);
};
MarkovGenerater::MarkovGenerater()
{
    //为什么我只能把这个放到构造函数里
    std::uniform_real_distribution<double> rnd(0, 1);
    rnd_ = rnd;
    //表示所有的模型都没有设定
    set_velocity = false;
    set_note = false;
    set_time = false;
    //默认数据
    fixed_velocity = 100;
    fixed_note = 75;
    fixed_time = 480;
}

//设置无模型的默认数据
void MarkovGenerater::set_fixed_note(unsigned short note)
{
    if (note > 127) {
        return;
    }
    fixed_note = note;
}
void MarkovGenerater::set_fixed_velocity(unsigned short velocity)
{
    if (velocity > 127) {
        return;
    }
    fixed_velocity = velocity;
}
void MarkovGenerater::set_fixed_time(unsigned short time)
{
    //time的单位是ms
    fixed_time = time;
}

//从指定文件读取模型数据
void MarkovGenerater::set_module_note(const char* filename)
{
    get_matrix(filename, index_note, vec1_note, vec2_note);
    set_note = true;
    return;
}
void MarkovGenerater::set_module_velocity(const char* filename)
{
    get_matrix(filename, index_velocity, vec1_velocity, vec2_velocity);
    set_velocity = true;
    return;
}
void MarkovGenerater::set_module_time(const char* filename)
{
    get_matrix(filename, index_time, vec1_time, vec2_time);
    set_time = true;
    return;
}

void MarkovGenerater::set_seed(double seed)
{
    rnd_engine.seed(seed);
}

unsigned short MarkovGenerater::play_note(Note midi_note, unsigned short instrument = 0, unsigned short channel = 0)
//直接播放声音.输出对应的持续时间(ms)
{
    unsigned short note, velocity, time;

    if (set_note) {
        note = get_value(stk_note, index_note, vec1_note, vec2_note);
    }
    else
    {
        note = fixed_note;
    }

    if (set_velocity) {
        velocity = get_value(stk_velocity, index_velocity, vec1_velocity, vec2_velocity);
    }
    else
    {
        velocity = fixed_velocity;
    }

    if (set_time) {
        time = get_value(stk_time, index_time, vec1_time, vec2_time);
    }
    else
    {
        time = fixed_time;
    }

    midi_note.play_note(note, velocity, instrument, channel);

    return time;
}

unsigned short MarkovGenerater::get_value(std::stack<unsigned short> stk, std::vector<unsigned short>& index, std::vector<double>& vec1, std::vector<std::vector<double>>& vec2)
//输出指定的状态
{
    unsigned short state_temp;
    if (stk.empty()) {
        //没有前置状态的情况
        state_temp = rnd_get(vec1);
        stk.push(state_temp);
        return index.at(state_temp);
    }
    else
    {
        state_temp = rnd_get(vec2.at(stk.top()));
        stk.pop();
        stk.push(state_temp);
        return index.at(state_temp);
    }
}

unsigned short MarkovGenerater::rnd_get(std::vector<double> p_vec)
//按指定的概率权重返回概率序列
//必须保证所提供的概率分布之和为一(因为程序不进行检查)
{
    double temp = rnd_(rnd_engine), total = 0;
    unsigned short index = 0;
    while (true) {
        total += p_vec.at(index);
        if (temp < total) {
            return index;
        }
        index += 1;
    }
}

void MarkovGenerater::get_matrix(const char* filename, std::vector<unsigned short>& index, std::vector<double>& vec1, std::vector<std::vector<double>>& vec2)
//从指定文件读取矩阵并分别存储到vec1,vec2中
{
    unsigned short size = 0, state = 0;
    std::ifstream file_stream;
    std::string temp_line, temp_str;

    //读取文件
    file_stream.open(filename, std::ios::in);
    if (file_stream.fail()) {
        //文件打开失败
        return;
    }
    //逐行读取
    while (getline(file_stream, temp_line, '\n')) {
        switch (state)
        {
        case 0:
        {
            size = std::stoi(temp_line);
            state++;
            break;
        }
        case 1:
        {
            //读取一维矩阵
            std::istringstream is(temp_line);
            for (unsigned short i = 0; i < size; i++) {
                is >> temp_str;
                index.push_back(std::stoi(temp_str));
            }
            state++;
            break;
        }
        case 2:
        {
            size = std::stoi(temp_line);
            state++;
            break;
        }
        case 3:
        {
            //读取一维矩阵
            std::istringstream is(temp_line);
            for (unsigned short i = 0; i < size; i++) {
                is >> temp_str;
                vec1.push_back(std::stod(temp_str));
            }
            state++;
            break;
        }
        case 4:
        {
            size = std::stoi(temp_line);
            state++;
            break;
        }
        case 5:
        {
            unsigned short row = 0;     //这是目前已经读取的行数
            std::vector<double> temp_vec1;

            //读取二维矩阵
            std::istringstream is(temp_line);
            for (unsigned short i = 0; i < size; i++) {
                is >> temp_str;
                temp_vec1.push_back(std::stod(temp_str));
            }
            row++;
            vec2.push_back(temp_vec1);

            if (row == size) {
                //只有读取完所有行才到下一个状态
                state++;
            }
            break;
        }
        default:
            //所有状态都处理完了
            break;
        }
    }

    file_stream.close();
    return;
}

void MarkovGenerater::print_matrix(void)
{
    for (auto i = vec1_velocity.begin(); i != vec1_velocity.end(); i++)
    {
        std::cout << *i << ' ';
    }
    std::cout << std::endl << std::endl;
    for (auto j = vec2_velocity.begin(); j != vec2_velocity.end(); j++)
    {
        for (auto i = (*j).begin(); i != (*j).end(); i++)
        {
            std::cout << *i << ' ';
        }
        std::cout << std::endl;
    }
}
