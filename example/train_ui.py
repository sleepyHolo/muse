# -*- coding: utf-8 -*-

import os
import time
import traceback
import numpy as np
import tkinter as tk
from tkinter import ttk

class TrainGUI():
    def __init__(self, window, log):
        self.window = window
        self.log = log
        
        # 导入训练使用的函数
        from train import get_data, add_count, save_model
        self.get_data = get_data
        self.add_count = add_count
        self.save_model = save_model
        
        self.data_dict = {}
        self.files_to_load = []
        self.loading = True
        self.set_ui()
    
    def set_ui(self):
        """设置训练界面"""
        ttk.Label(self.window, text = 'Train A Model',
                  style = 'wTitle.TLabel').place(relx = 0.03, rely = 0.03)
        ttk.Label(self.window, text = 'Name',
                  style = 'wTitle2.TLabel').place(relx = 0.05, rely = 0.12)
        self.output_name = ttk.Entry(self.window, style = 'wTitle.TEntry',
                                     show = None)
        self.output_name.place(relx = 0.15, rely = 0.12, height = 40)
        
        # 设置treeview
        self.input_tree = ttk.Treeview(self.window)
        self.input_tree.place(relx = 0.05, rely = 0.2, 
                              relwidth = 0.8, relheight = 0.4)
        self.input_tree['show'] = 'headings'
        self.input_tree['columns'] = ('File', 'State')
        # 设置列
        self.input_tree.column('File', width = 600)
        self.input_tree.heading('File', text = 'File')
        self.input_tree.column('State', width = 200, anchor = 'center')
        self.input_tree.heading('State', text = 'State')
        
        '''
        for key in self.channel.keys():
            self.channel_tree.insert('', 'end', 
                                     values = (key, self.channel[key]))
            '''
            
        # 导入单个.mid文件
        ttk.Label(self.window, text = 'File',
                  style = 'wTitle2.TLabel').place(relx = 0.08, rely = 0.65)
        self.file_path = tk.StringVar()
        self.file_entry = ttk.Entry(self.window, 
                                    textvariable = self.file_path)
        self.file_entry.place(relx = 0.15, rely = 0.65, relwidth = 0.65)
        self.file_button = ttk.Button(self.window, text = 'Select',
                                      command = self.file_select)
        self.file_button.place(relx = 0.82, rely = 0.65, relwidth = 0.1)
        
        # 导入整个文件夹
        ttk.Label(self.window, text = 'Dir',
                  style = 'wTitle2.TLabel').place(relx = 0.08, rely = 0.70)
        self.dir_path = tk.StringVar()
        self.dir_entry = ttk.Entry(self.window, 
                                   textvariable = self.dir_path)
        self.dir_entry.place(relx = 0.15, rely = 0.70, relwidth = 0.65)
        self.dir_button = ttk.Button(self.window, text = 'Select',
                                      command = self.dir_select)
        self.dir_button.place(relx = 0.82, rely = 0.70, relwidth = 0.1)
        
        # 控制按钮
        self.button_insert = ttk.Button(self.window, text = 'Insert',
                                        command = self.insert)
        self.button_insert.place(relx = 0.82, rely = 0.75, relwidth = 0.1)
        
        self.text_insert_switch = tk.StringVar()
        self.text_insert_switch.set('Stop')
        self.insert_switch = ttk.Button(self.window, 
                                        textvariable = self.text_insert_switch,
                                        command = self.switch_insert)
        self.insert_switch.place(relx = 0.70, rely = 0.75, relwidth = 0.1)
        
        # 设置训练button
        self.train_button = ttk.Button(self.window, style = 'wTitle.TButton',
                                       text = 'Train', command = self.train)
        self.train_button.place(relx = 0.85, rely = 0.9, 
                                relwidth = 0.1, relheight = 0.05)
        
        # 设置清除数据button
        self.clear_button = ttk.Button(self.window, text = 'Clear', 
                                       command = self.clear)
        self.clear_button.place(relx = 0.70, rely = 0.92, relwidth = 0.1)
    
    def file_select(self):
        """允许用户选择文件"""
        path = tk.filedialog.askopenfilename(title = 'Select A MID File', 
                                    initialdir = './',
                                    filetypes = (('midi files', '*.mid'),))
        self.file_path.set(path)
        return
    
    def dir_select(self):
        """选择文件夹"""
        path = tk.filedialog.askdirectory(title = 'Select A MID File', 
                                          initialdir = './')
        self.dir_path.set(path)
        return
    
    def insert(self):
        """给button_insert用的"""
        if (path := self.file_path.get()):
            self.files_to_load.append(path)
            self.file_insert()
            self.file_path.set('')
        if (dir_path := self.dir_path.get()):
            self.dir_insert(dir_path)
            self.dir_path.set('')
        return
    
    def switch_insert(self):
        self.loading = not self.loading
        if self.loading:
            self.text_insert_switch.set('Stop')
            self.file_insert()
        else:
            self.text_insert_switch.set('Load')
    
    def dir_insert(self, path):
        """遍历文件夹下mid文件,不遍历子文件夹"""
        files = []
        for file in os.listdir(path):
            if os.path.isdir(os.path.join(path, file)):
                continue
            name, extension = os.path.splitext(file)
            if extension == '.mid':
                files.append(os.path.join(path, file))
        for file in files:
            self.files_to_load.append(file)
        self.file_insert()
    
    def file_insert(self):
        """
        插入指定文件,需要提供文件路径-现在自动载入文件路径
        用after改成异步试试?异步真香
        """
        try:
            # FILO结构
            path = self.files_to_load.pop()
        except:
            return
        
        if path in self.data_dict:
            # 存在已有值的情况
            item = self.data_dict[path]['item']
            self.input_tree.item(item, values = (path, 'Not Loaded'))
            self.data_dict[path]['state'] = 'Not Loaded'
            self.read_file(path)
            return
        else:
            # 新项目的情况
            item = self.input_tree.insert('', 'end', 
                                          values = (path, 'Not Loaded'))
            self.data_dict[path] = {'state': 'Not Loaded', 'item': item}
            self.read_file(path)
        
        if self.files_to_load: 
            if self.loading:
                self.window.after(5, self.file_insert)
        else:
            self.log.log_add('*highLoaded all target files.*norm\n')
        
        return
    
    def read_file(self, path):
        """读取文件"""
        try:
            data = self.get_data(path)
            self.data_dict[path]['data'] = data
        except:
            self.log.log_add('*erroError:*norm Loading: {}'.format(path),
                             show_time = True, end = '\n')
            self.log.log_add(traceback.format_exc(), end = '\n')
        else:
            self.data_dict[path]['state'] = 'Loaded'
            self.input_tree.item(self.data_dict[path]['item'], 
                                 values = (path, 'Loaded'))
            self.log.log_add('Train - Load a midi file: {}'.format(path),
                             show_time = True, end = '\n')
    
    def count_files(self):
        """统计所有文件的数据"""
        data = []
        for path in self.data_dict.keys():
            if self.data_dict[path]['state'] == 'Loaded':
                data.append(self.data_dict[path]['data'])
                self.log.log_add('Load data: {}'.format(path), end = '\n')
        return self.add_count(*data), len(data)
    
    def clear(self):
        """清除所有已载入的文件"""
        del self.data_dict
        self.data_dict = {}
        for item in self.input_tree.get_children():
            self.input_tree.delete(item)
        self.log.log_add('Clear all loaded files.', show_time = True,
                         end = '\n')
    
    def train(self):
        if (name := self.output_name.get()) == '':
            name = 'output'
        self.log.log_add('Train models: {}'.format(name), show_time = True,
                         end = '\n')
        data, num = self.count_files()
        if num == 0:
            self.log.log_add(f'*warnWarning:*norm No file: Models {name}',
                             end = '\n')
            return
        
        # 训练模型
        self.temp_num = num
        self.asyn_train(data, step_size = 5000, name = name,
                        reset = True)
    
    def asyn_train(self, data, step_size = 500, name = 'output', number = 12,
                   reset = False, index = -1, 
                   options = ['note', 'velocity', 'time'],
                   start_time = -1, type_size = -1, 
                   type_index = {}, data_size = -1, pre_state = -1, 
                   statistic_1 = np.zeros(1), statistic_2 = np.zeros(1)):
        """
        允许使用伪异步化的训练,每训练至多step_size个数据输出一次
        传前4个,后面的参数不要写
        """
        if reset:
            index += 1
            reset = False
            
            pre_state = -1
            start_time = time.time()
            type_size = len(data['type'][index])
            data_size = len(data['list'][index])
            
            # 开始训练
            statistic_1 = np.zeros(type_size)
            statistic_2 = np.zeros((type_size, type_size))
            # 由于取数据用的pop,需要把原始数据反向
            data['list'][index].reverse()
        
            # 建立type_index
            for num in data['type'][index]:
                type_index[num] = data['type'][index].index(num)
        
        remain_data = len(data['list'][index])
        
        for i in range(min(step_size, remain_data)):
            state = int(data['list'][index].pop())
            
            statistic_1[type_index[state]] += 1
            if pre_state != -1:
                statistic_2[type_index[pre_state]][type_index[state]] += 1
            pre_state = state
        
        # 输出log,计算进度和剩余时间
        percentage = 1 - len(data['list'][index]) / data_size
        remaining_time = (time.time() - start_time) * (1 / percentage - 1)
        self.log.log_add(f'Training model({options[index]}): '
                         f'{100*percentage:.2f}%\n'
                         f'\tRemaining time: {remaining_time:.3f}s\n')
        
        if data['list'][index] == []:
            # 结束统计
            p_mat_1 = statistic_1 / data_size
            p_mat_2 = np.zeros((type_size, type_size))
            for row in range(type_size):
                p_mat_2[row] = statistic_2[row] / sum(statistic_2[row])
            # save
            self.save_model(data['type'][index], p_mat_1, p_mat_2, 
                            number = number,
                            filename = f'{name}_{options[index]}')
            self.log.log_add(f'Trained model({options[index]}), '
                             f'total time: {time.time()-start_time:.3f}s\n')
            reset = True
            
            if index == 2:
                self.log.log_add(f'Saved models: {name}_note.model, '
                                 f'{name}_velocity.model, '
                                 f'{name}_time.model. '
                                 f'Using {self.temp_num} files.', end = '\n')
                del self.temp_num
                return
        
        # 使用after工作
        self.window.after(10,
                          lambda: self.asyn_train(data, step_size, name, 
                                                  number, reset, index, 
                                                  options, start_time, 
                                                  type_size, type_index, 
                                                  data_size, pre_state, 
                                                  statistic_1, statistic_2))
        return
        
        