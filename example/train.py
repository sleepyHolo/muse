# -*- coding: utf-8 -*-

import numpy as np
import mido
import argparse
import os


def send_msg(file_name):
    """读取指定midi文件的所有信息"""
    mid = mido.MidiFile(file_name)
    for i, track in enumerate(mid.tracks):
        print('Track {}: {}'.format(i, track.name))
        for msg in track:
            # 输出每个动作.
            print(msg)


def read_midi(file_name):
    """读取note, velocity, time(ms)"""
    mid = mido.MidiFile(file_name)

    all_tracks = {}
    # 这里tracks代表了音轨的东西,每条音轨通常情况下就是一个乐器.
    for index, track in enumerate(mid.tracks):
        temp = []
        for msg in track:
            temp_msg = str(msg).split()
            if temp_msg[0] == 'note_on':
                if int(temp_msg[4].split('=')[1]) != 0:
                    # 如果note_on的时间不为0,以休止符的形式记录它
                    # 读取音符数据
                    temp_note = [0]
                    for i in range(3, 5):
                        temp_note.append(int(temp_msg[i].split('=')[1]))
                    temp.append(temp_note)
            
            if temp_msg[0] == 'note_off':
                # 读取音符数据
                temp_note = []
                for i in range(2, 5):
                    temp_note.append(int(temp_msg[i].split('=')[1]))
                temp.append(temp_note)
        all_tracks['track_' + str(index)] = temp

    return all_tracks


def counter(track):
    """统计note, velocity, time的总数"""
    note_types = []
    velocity_types = []
    time_types = []

    note_list = []
    velocity_list = []
    time_list = []

    for note in track:
        note_list.append(note[0])
        velocity_list.append(note[1])
        time_list.append(note[2])

        if not note[0] in note_types:
            note_types.append(note[0])
        if not note[1] in velocity_types:
            velocity_types.append(note[1])
        if not note[2] in time_types:
            time_types.append(note[2])

    note_types.sort()
    velocity_types.sort()
    time_types.sort()
    return {'type': [note_types, velocity_types, time_types],
            'list': [note_list, velocity_list, time_list]}


def add_count(*args):
    """合并不同的统计结果.输入应该是函数counter的返回值"""
    if not args:
        return
    ans = args[0]

    for i in range(1, len(args)):
        # note type
        for type_index in args[i]['type'][0]:
            if not type_index in ans['type'][0]:
                ans['type'][0].append(type_index)
        # velocity type
        for type_index in args[i]['type'][1]:
            if not type_index in ans['type'][1]:
                ans['type'][1].append(type_index)
        # time type
        for type_index in args[i]['type'][2]:
            if not type_index in ans['type'][2]:
                ans['type'][2].append(type_index)
        
        # 给index排序
        ans['type'][0].sort()
        ans['type'][1].sort()
        ans['type'][2].sort()
        
        # 合并list
        ans['list'][0] += args[i]['list'][0]
        ans['list'][1] += args[i]['list'][1]
        ans['list'][2] += args[i]['list'][2]

    return ans


def get_data(filename):
    """读取某一个midi文件.返回值可以直接训练也可以使用add_count与其他数据合并"""
    temp = []
    for track in read_midi(filename).values():
        temp.append(counter(track))

    return add_count(*temp)


def train(types, data_list):
    """训练Markov链"""
    state_num = len(types)
    total = len(data_list)
    # 制作索引的字典
    type_index = {}
    for num in types:
        type_index[num] = types.index(num)

    statistic_1 = np.zeros(state_num)
    statistic_2 = np.zeros((state_num, state_num))

    # 训练
    pre_state = -1
    for i in range(total):
        state = int(data_list[i])

        statistic_1[type_index[state]] += 1
        if pre_state != -1:
            statistic_2[type_index[pre_state]][type_index[state]] += 1
        pre_state = state

    p_mat_1 = statistic_1 / total
    p_mat_2 = np.zeros((state_num, state_num))
    for row in range(state_num):
        p_mat_2[row] = statistic_2[row] / sum(statistic_2[row])

    return p_mat_1, p_mat_2

def save_model(*args, **kargs):
    """
    types, p_mat_1, p_mat_2
    小数点位数number=, 输出到文件filename=
    文件后缀为.model不需要输入后缀
    由于函数自动补位的原因,由科学计数法保留的数据的输出是错误的
    """
    state_num = len(args[0])

    result = str(state_num) + '\n'
    temp = []
    for type_value in args[0]:
        temp.append(str(type_value))
    result += ' '.join(temp) + '\n'

    if (number := kargs.get('number', None)):
        # 处理p_mat_1
        result += str(state_num) + '\n'
        temp = []
        for num in args[1]:
            temp.append(f'{num:.{number}f}')
        result += ' '.join(temp) + '\n'

        # 处理p_mat_2
        result += str(state_num) + '\n'
        for row in args[2]:
            temp = []
            for num in row:
                temp.append(f'{num:.{number}f}')
            result += ' '.join(temp) + '\n'
    else:
        # 处理p_mat_1
        result += str(state_num) + '\n'
        temp = []
        for num in args[1]:
            temp.append(str(num))
        result += ' '.join(temp) + '\n'

        # 处理p_mat_2
        result += str(state_num) + '\n'
        for row in args[2]:
            temp = []
            for num in row:
                temp.append(str(num))
            result += ' '.join(temp) + '\n'

    if (filename := kargs.get('filename', None)):
        file = open(filename + '.model', 'w')
        file.write(result)
        file.close()
    else:
        print(result)

def train_and_save(data, output_name = 'output', number = 12):
    """训练指定的序列数据.保存为三个model文件"""
    # train note model
    temp_p1, temp_p2 = train(data['type'][0], data['list'][0])
    save_model(data['type'][0], temp_p1, temp_p2, number = number,
               filename = output_name + '_note')
    # train velocity model
    temp_p1, temp_p2 = train(data['type'][1], data['list'][1])
    save_model(data['type'][1], temp_p1, temp_p2, number = number,
               filename = output_name + '_velocity')
    # train time model
    temp_p1, temp_p2 = train(data['type'][2], data['list'][2])
    save_model(data['type'][2], temp_p1, temp_p2, number = number,
               filename = output_name + '_time')

# 代表主函数
if __name__ == '__main__':
    # 命令行参数
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', type = str, default = None,
                        help = 'Name of the MIDI file you want to deal with.')
    parser.add_argument('--dir', type = str, default = None,
                        help = 'Dir of the MIDI file you want to deal with.' +\
                            ' All MIDI file will be used to train.')
    parser.add_argument('--output', type = str, default = 'output',
                        help = 'Name of output file. Default: output.' +\
                            ' No extension.')
    parser.add_argument('--number', type = int, default = 12,
                        help = 'Number of decimal places model accurate to.')
    
    args = parser.parse_args()
    
    if args.file:
        name, extension = os.path.splitext(args.file)
        if not extension == '.mid':
            print('Not a midi file.')
        else:
            train_and_save(get_data(args.file), args.output, args.number)
    if args.dir:
        path = os.path.join('./', args.dir)
        files = []
        for file in os.listdir(path):
            if os.path.isdir(os.path.join(path, file)):
                continue
            name, extension = os.path.splitext(file)
            if extension == '.mid':
                files.append(os.path.join(path, file))
        if files:
            data = []
            for file in files:
                data.append(get_data(file))
            
            train_and_save(add_count(*data), args.output, args.number)
        else:
            print('No midi file in given dir.')
    
    if args.file == None and args.dir == None:
        print("Should use '--file' or '--dir'.")
    else:
        print('Done.')
