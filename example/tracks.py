# -*- coding: utf-8 -*-

import os
import time
import tkinter as tk
from tkinter import ttk
import tkinter.filedialog
import muse

class MusicPlayer():
    """管理多音轨"""
    def __init__(self, window, log):
        self.window = window
        self.log = log
        
        self.midi_note = muse.Note()
        self.set_notebook()
        self.load_instruments()
    
    def __del__(self):
        if self.midi_note_open.get() == 'Open':
            self.midi_note.close()
        del self.midi_note
        for track in self.tracks:
            del track
    
    def set_notebook(self):
        """设置初始notebook及其frame"""
        self.tracks = []
        self.channel = {}
        for i in range(16):
            self.channel['Channel_{}'.format(str(i))] = 'Available'
        
        self.new_track_avail = True
        
        self.track_notebook = ttk.Notebook(self.window)
        self.track_notebook.place(relx = 0, rely = 0,
                                relwidth = 1, relheight = 1)
        
        # 这是其tab页面,全部都是ttk.Frame.使用add是为了方便添加页面标签
        self.new_label_text = tk.StringVar()
        self.set_text_out()
        self.tab_new = ttk.Frame(None, style = 'wR.TFrame')
        self.tab_new_label = ttk.Label(self.tab_new, 
                                       textvariable = self.new_label_text,
                                       style = 'wTitle.TLabel')
        self.tab_new_label.place(relx = 0.03, rely = 0.03)
        
        # 可输入的名字
        ttk.Label(self.tab_new, text = 'Name',
                  style = 'wTitle2.TLabel').place(relx = 0.05, rely = 0.12)
        self.track_name = ttk.Entry(self.tab_new, style = 'wTitle.TEntry',
                                    show = None)
        self.track_name.place(relx = 0.15, rely = 0.12, height = 40)
        
        # 设置treeview
        self.channel_tree = ttk.Treeview(self.tab_new)
        self.channel_tree.place(relx = 0.05, rely = 0.2, 
                                relwidth = 0.5, relheight = 0.4)
        self.channel_tree['show'] = 'headings'
        self.channel_tree['columns'] = ('Channel', 'State')
        for col in ('Channel', 'State'):
            self.channel_tree.column(col, anchor = 'center')
            self.channel_tree.heading(col, text = col)
        
        for key in self.channel.keys():
            self.channel_tree.insert('', 'end',
                                     values = (key, self.channel[key]))
        
        # 设置midi控制按钮
        self.midi_note_open = tk.StringVar()
        self.midi_note_open.set('Open')
        self.midi_note.open()
        self.midi_button = ttk.Checkbutton(self.tab_new, text = 'MIDI-Open',
                                           variable = self.midi_note_open,
                                           onvalue = 'Open', 
                                           offvalue = 'Close')
        self.midi_button.place(relx = 0.05, rely = 0.65)
        self.midi_button.bind('<Button-1>', self.midi_switch)
        
        # 设置新建&删除button
        self.new_button = ttk.Button(self.tab_new, style = 'wTitle.TButton',
                                     text = '+', command = self.new_track)
        self.new_button.place(relx = 0.85, rely = 0.9, 
                              relwidth = 0.1, relheight = 0.05)
        self.del_button = ttk.Button(self.tab_new, style = 'wTitle.TButton',
                                     text = '-', command = self.del_track)
        self.del_button.place(relx = 0.7, rely = 0.9, 
                              relwidth = 0.1, relheight = 0.05)
        
        self.track_notebook.add(self.tab_new, text = '+NEW', padding = '0.05i')
    
    def new_track(self):
        """新建一个音轨"""
        if not self.new_track_avail:
            return
        track_frame = ttk.Frame(None, style = 'wR.TFrame')
        
        if not (name := self.track_name.get()):
            name = 'track_' + str(1 + len(self.tracks))
        
        # 获取目标channel
        if (items := self.channel_tree.selection()):
            item_text = self.channel_tree.item(items[0], 'values')
            if (state := item_text[1]) == 'Available':
                channel = item_text[0].split('_')[1]
                # 修改占用情况
                self.channel_tree.item(items[0], values = (item_text[0], name))
        if not (bool(items) and state == 'Available'):
            for item in self.channel_tree.get_children():
                item_text = self.channel_tree.item(item, 'values')
                if item_text[1] == 'Available':
                    channel = item_text[0].split('_')[1]
                    # 修改占用情况
                    self.channel_tree.item(item, values = (item_text[0], name))
                    break
        
        self.track_notebook.add(track_frame, text = name, padding = '0.05i')
        # 显示新建页面
        self.track_notebook.select(track_frame)
        
        self.tracks.append(Track(track_frame, name, channel,
                                 self.instruments, self.instruments_id,
                                 self.log, self.midi_note,
                                 self.midi_state_get()))
        
        self.set_text_out()
        self.log.log_add('Create a track: '+\
                         '{} (using Channel_{})'.format(name, channel),
                         show_time = True, end = '\n')
    
    def del_track(self):
        """删除指定位置的非空音轨"""
        # 根据channel删除
        if (items := self.channel_tree.selection()):
            item_text = self.channel_tree.item(items[0], 'values')
            if (state := item_text[1]) == 'Available':
                return
            for i in range(self.track_notebook.index(tk.END)):
                if state == (name := self.track_notebook.tab(i, 'text')):
                    for id_, track in enumerate(self.tracks):
                        if track.name == name:
                            self.tracks.pop(id_)
                            track.pause()
                            del track
                            channel = item_text[0].split('_')[1]
                            self.log.log_add(f'Delete a track: {name}'
                                             f' (using Channel_{channel})',
                                             show_time = True, end = '\n')
                            break
                    self.track_notebook.forget(i)
                    # 修改占用情况
                    self.channel_tree.item(items[0], values = (item_text[0], 
                                                               'Available'))
                    break
                
        
    
    def set_text_out(self):
        """根据现有的音轨数量创建标签输出"""
        num = len(self.tracks)
        if num == 0:
            text = 'No Track '
        else:
            text = '{} Track'.format(str(num))
            if num == 1:
                text += ' '
            else:
                text += 's '
        text += 'Available. '
        if num == 16:
            self.new_track_avail = False
        else:
            self.new_track_avail = True
            text += 'Create a new one.'
        self.new_label_text.set(text)
    
    def load_instruments(self):
        """从保存文件中加载乐器"""
        self.instruments = {}
        self.instruments_id = []
        with open('./GeneralMIDI.txt', 'r') as file:
            line = file.readline()
            index = 0
            while line:
                self.instruments[line] = index
                self.instruments_id.append(line)
                index += 1
                line = file.readline()
        return
    
    def midi_switch(self, event):
        """控制midi_note的状态"""
        if self.midi_note_open.get() == 'Open':
            self.midi_note.close()
            self.log.log_add('Closed Midi', show_time = True, end = '\n')
            for track in self.tracks:
                track.midi_open = False
        else:
            self.midi_note.open()
            self.log.log_add('Opened Midi', show_time = True, end = '\n')
            for track in self.tracks:
                track.midi_open = True
    
    def midi_state_get(self):
        if self.midi_note_open.get() == 'Open':
            return True
        else:
            return False
        
class Track():
    """提供声音控件"""
    def __init__(self, window, name, channel, instruments, instruments_id,
                 log, midi_note, midi_open):
        self.window = window
        self.name = name
        self.channel = channel
        self.instruments = instruments
        self.instruments_id = instruments_id
        self.log = log
        self.midi_note = midi_note
        self.midi_open = midi_open
        
        self.generator = muse.MarkovGenerator()
        self.is_playing = False
        
        self.set_gui()
    
    def __del__(self):
        del self.generator
    
    def set_midi_state(self, midi_open):
        self.midi_open = midi_open
    
    def set_gui(self):
        ttk.Label(self.window, text = self.name,
                  style = 'wTitle.TLabel').place(relx = 0.03, rely = 0.03)
        ttk.Label(self.window, text = 'Channel  {}'.format(str(self.channel)),
                  style = 'wTitle2.TLabel').place(relx = 0.05, rely = 0.1)
        
        # 设置乐器表单
        ttk.Label(self.window, text = 'Instrument',
                  style = 'wTitle2.TLabel').place(relx = 0.05, rely = 0.15)
        self.ins_com = ttk.Combobox(self.window, state = 'readonly')
        self.ins_com.place(relx = 0.25, rely = 0.15, relwidth = 0.4)
        self.ins_com['value'] = self.instruments_id
        self.ins_com.current(0)
        self.instrument = 0
        self.ins_com.bind('<<ComboboxSelected>>', self.set_instrument)
        
        # 设置模型
        ttk.Label(self.window, text = 'Models',
                  style = 'wTitle.TLabel').place(relx = 0.05, rely = 0.22)
        
        # note
        ttk.Label(self.window, text = 'Note',
                  style = 'wTitle2.TLabel').place(relx = 0.08, rely = 0.30)
        self.note_model = tk.StringVar()
        self.note_entry = ttk.Entry(self.window, 
                                    textvariable = self.note_model)
        self.note_entry.place(relx = 0.2, rely = 0.30, relwidth = 0.6)
        self.note_button = ttk.Button(self.window, text = 'Select',
                            command = lambda: self.file_select('note'))
        self.note_button.place(relx = 0.82, rely = 0.30, relwidth = 0.1)
        
        ttk.Label(self.window, text = 'Default',
                  style = 'wTitle2.TLabel').place(relx = 0.2, rely = 0.35)
        self.note_com = ttk.Combobox(self.window, state = 'readonly')
        self.note_com.place(relx = 0.3, rely = 0.35, relwidth = 0.2)
        self.note_com['value'] = list(range(128))
        self.note_com.current(75)
        
        # velocity
        ttk.Label(self.window, text = 'Velocity',
                  style = 'wTitle2.TLabel').place(relx = 0.08, rely = 0.40)
        self.velocity_model = tk.StringVar()
        self.velocity_entry = ttk.Entry(self.window, 
                                    textvariable = self.velocity_model)
        self.velocity_entry.place(relx = 0.2, rely = 0.40, relwidth = 0.6)
        self.velocity_button = ttk.Button(self.window, text = 'Select',
                            command = lambda: self.file_select('velocity'))
        self.velocity_button.place(relx = 0.82, rely = 0.40, relwidth = 0.1)
        
        ttk.Label(self.window, text = 'Default',
                  style = 'wTitle2.TLabel').place(relx = 0.2, rely = 0.45)
        self.velocity_com = ttk.Combobox(self.window, state = 'readonly')
        self.velocity_com.place(relx = 0.3, rely = 0.45, relwidth = 0.2)
        self.velocity_com['value'] = list(range(128))
        self.velocity_com.current(100)
        
        # time
        ttk.Label(self.window, text = 'Time',
                  style = 'wTitle2.TLabel').place(relx = 0.08, rely = 0.50)
        self.time_model = tk.StringVar()
        self.time_entry = ttk.Entry(self.window, 
                                    textvariable = self.time_model)
        self.time_entry.place(relx = 0.2, rely = 0.50, relwidth = 0.6)
        self.time_button = ttk.Button(self.window, text = 'Select',
                            command = lambda: self.file_select('time'))
        self.time_button.place(relx = 0.82, rely = 0.50, relwidth = 0.1)
        
        ttk.Label(self.window, text = 'Default',
                  style = 'wTitle2.TLabel').place(relx = 0.2, rely = 0.55)
        self.time_default_entry = ttk.Entry(self.window)
        self.time_default_entry.place(relx = 0.3, rely = 0.55, 
                                      relwidth = 0.3)
        ttk.Label(self.window, text = 'ms',
                  style = 'wNorm.TLabel').place(relx = 0.61, rely = 0.555)
        
        # seed
        ttk.Label(self.window, text = 'Seed',
                  style = 'wTitle2.TLabel').place(relx = 0.08, rely = 0.60)
        self.seed_str = tk.StringVar()
        self.seed_var = tk.StringVar()
        
        ttk.Label(self.window, textvariable = self.seed_var,
                  style = 'wNorm.TLabel').place(relx = 0.2, rely = 0.605)
        self.seed_entry = ttk.Entry(self.window, 
                                    textvariable = self.seed_str)
        self.seed_entry.place(relx = 0.45, rely = 0.60, relwidth = 0.35)
        self.seed_button = ttk.Button(self.window, text = 'Set', 
                                      command = self.set_seed)
        self.seed_button.place(relx = 0.82, rely = 0.6, relwidth = 0.1)
        # 最后设置seed
        self.set_seed(False)
        
        # load
        self.load_button = ttk.Button(self.window, text = 'Load', 
                                      command = self.load_models)
        self.load_button.place(relx = 0.82, rely = 0.68, relwidth = 0.1)
        
        # play music
        self.play_button = ttk.Button(self.window, style = 'wTitle2.TButton',
                                     text = 'Play', command = self.play)
        self.play_button.place(relx = 0.85, rely = 0.9, 
                               relwidth = 0.1, relheight = 0.05)
        # pause music
        self.pause_button = ttk.Button(self.window, style = 'wTitle2.TButton',
                                       text = 'Pause', command = self.pause)
        self.pause_button.place(relx = 0.7, rely = 0.9, 
                                relwidth = 0.1, relheight = 0.05)
        self.pause_button.config(state = tk.DISABLED)
    
    def file_select(self, option):
        """允许用户选择文件"""
        path = tk.filedialog.askopenfilename(title = 'Select A Model', 
                                    initialdir = './',
                                    filetypes = (('model files', '*.model'),))
        if option == 'note':
            self.note_model.set(path)
            return
        
        if option == 'velocity':
            self.velocity_model.set(path)
            return
        
        if option == 'time':
            self.time_model.set(path)
            return
    
    def set_seed(self, report = True):
        if not (seed_str := self.seed_entry.get()):
            seed_str = str(time.time())
        self.seed = hash(seed_str)
        self.seed_var.set(str(self.seed))
        # 设置随机种子
        try:
            self.generator.set_seed(self.seed)
        except:
            self.log.log_add('*erroUnknownError:*norm Failed to '+\
                             'set {} - Seed: {}'.format(self.name, self.seed),
                             show_time = True, end = '\n')
        else:
            if report:
                self.log.log_add('Set {} - Seed: {}'.format(self.name, 
                                                            self.seed),
                                 show_time = True, end = '\n')
    
    def load_models(self):
        """载入模型"""
        self.log.log_add('Loading {} - Models'.format(self.name),
                         show_time = True, end = '\n')
        default = [False, False, False]
        if (note_path := self.note_entry.get()):
            state = self.load(note_path, 'note')
        if not (note_path and state):
            if (note_default := self.note_com.get()):
                self.generator.set_fixed_note(int(note_default))
                default[0] = True
        
        if (velocity_path := self.velocity_entry.get()):
            state = self.load(velocity_path, 'velocity')
        if not (velocity_path and state):
            if (velocity_default := self.velocity_com.get()):
                self.generator.set_fixed_velocity(int(velocity_default))
                default[1] = True
        
        if (time_path := self.time_entry.get()):
            state = self.load(time_path, 'time')
        if not (time_path and state):
            if (time_default := self.time_default_entry.get()):
                try:
                    self.generator.set_fixed_time(int(time_default))
                except:
                    self.log.log_add('*erroValueError:*norm Not a vaild ' +\
                                     'time (must ba a number):'+\
                                     ' {}'.format(time_default), end = '\n')
                else:
                    default[2] = True
            else:
                default[2] = True
        self.log.log_add('*highDone.*norm Default:')
        if default[0]:
            self.log.log_add(' note')
        if default[1]:
            self.log.log_add(' velocity')
        if default[2]:
            self.log.log_add(' time')
        self.log.log_add('\n')
    
    
    def load(self, path_, option):
        self.log.log_add('Loading model({}): {}'.format(option, path_))
        if os.access(path_, os.F_OK):
            if os.access(path_, os.R_OK):
                name, extension = os.path.splitext(path_)
                if extension == '.model':
                    if option == 'note':
                        self.generator.set_module_note(path_)
                        self.log.log_add('*high Done.*norm', end = '\n')
                        return True
                    if option == 'velocity':
                        self.generator.set_module_velocity(path_)
                        self.log.log_add('*high Done.*norm', end = '\n')
                        return True
                    if option == 'time':
                        self.generator.set_module_time(path_)
                        self.log.log_add('*high Done.*norm', end = '\n')
                        return True
                else:
                    self.log.log_add('\n*warnWarning:*norm This file is not' +\
                                     ' a model. If you really want to load' +\
                                     ' it, please change the extension: ' +\
                                     '\'{}\''.format(path_), end = '\n')
                    return False
            else:
                self.log.log_add('\n*erroIOError:*norm Unable to load file: '+\
                                 '\'{}\''.format(path_), end = '\n')
                return False
        else:
            self.log.log_add('\n*erroFileNotFoundError:*norm No such file or'+\
                             ' directory:  \'{}\''.format(path_), end = '\n')
            return False
    
    def set_instrument(self, event):
        """获取当前使用的乐器"""
        instrument_str = self.ins_com.get()
        self.instrument = self.instruments[instrument_str]
        self.log.log_add('Set {} - Instrument: {} (id {})'.format(self.name,
                                    instrument_str.rstrip(), self.instrument),
                         show_time = True, end = '\n')
        
    
    def play(self):
        """播放音乐"""
        if not self.is_playing:
            self.play_button.config(state = tk.DISABLED)
            self.pause_button.config(state = tk.NORMAL)
            self.is_playing = True
        
        if self.midi_open:
            time = self.generator.play_note(self.midi_note, self.instrument, 
                                            int(self.channel))
            self.after_id = self.window.after(time, self.play)
        else:
            self.log.log_add('\n*warnMidiWarning:*norm Midi is not open.\n')
            self.play_button.config(state = tk.NORMAL)
            self.pause_button.config(state = tk.DISABLED)
            self.is_playing = False
    
    def pause(self):
        if self.is_playing:
            self.play_button.config(state = tk.NORMAL)
            self.pause_button.config(state = tk.DISABLED)
            self.is_playing = False
        
        try:
            self.window.after_cancel(self.after_id)
        except Exception:
            self.log.log_add('\n*erroPauseError:*norm Failed to pause\n')