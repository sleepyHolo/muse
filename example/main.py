# -*- coding: utf-8 -*-

import time
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
try:
    import pyautogui
    pyautogui.FAILSAFE = False  # 可以阻止一些奇怪的缩放?
except Exception:
    pass

from tracks import MusicPlayer
from train_ui import TrainGUI


class MainDemoGui():
    """主Gui框架"""
    def __init__(self, window):
        self.window = window
        # 窗口设置
        self.window.title('Demo')
        self.window.geometry('1920x1080')
        #self.window.attributes('-topmost', 1)
        
        # 样式设计
        # 注意TFrame是ttk.Frame的默认样式,Frame的样式以.TFrame结束,其他同理
        self.styles = [
            ttk.Style().configure('wTitle.TLabel', background = 'white',
                                  relief = tk.FLAT, font = ('Arial', 20)),
            ttk.Style().configure('wTitle2.TLabel', background = 'white',
                                  relief = tk.FLAT, font = ('Arial', 14)),
            ttk.Style().configure('wNorm.TLabel', background = 'white',
                                  relief = tk.FLAT, font = ('Arial', 10)),
            ttk.Style().configure('wTitle.TButton', foreground = 'blue',
                                  relief = tk.RAISED, font = ('Arial', 20)),
            ttk.Style().configure('wTitle2.TButton', foreground = 'blue',
                                  relief = tk.RAISED, font = ('Arial', 14)),
            ttk.Style().configure('wTitle.TEntry', background = 'white',
                                  relief = tk.FLAT, font = ('Arial', 14)),
            ttk.Style().configure('wF.TFrame', background = 'white',
                                  relief = tk.FLAT),
            ttk.Style().configure('wR.TFrame', background = 'white',
                                  relief = tk.RAISED),
            ttk.Style().configure('TNotebook', background = 'white',
                                  relief = tk.RAISED),
            ttk.Style().configure('Treeview', background = 'white',
                                  relief = tk.SUNKEN, rowheight = 25),
            ttk.Style().configure('TCheckbutton', background = 'white',
                                  relief = tk.SUNKEN, font = ('Arial', 14)),
            ttk.Style().configure('wNorm.TCheckbutton', background = 'white',
                                  relief = tk.SUNKEN, font = ('Arial', 10))]
        
        self.set_window_frame()
        self.set_notebook()
    
    def __del__(self):
        del self.player
        del self.log
    
    def set_window_frame(self):
        """设置window级别的frame"""
        self.frame_log = ttk.Frame(self.window)
        self.frame_log.place(relx = 0.01, rely = 0.02,
                                relwidth = 0.4, relheight = 0.6)
        
        self.frame_notebook = ttk.Frame(self.window)
        self.frame_notebook.place(relx = 0.42, rely = 0.02,
                                  relwidth = 0.56, relheight = 0.96)
        
        self.log = Log(self.frame_log)
    
    def set_notebook(self):
        """设置右侧的notebook及其frame"""
        self.gui_notebook = ttk.Notebook(self.frame_notebook)
        self.gui_notebook.place(relx = 0, rely = 0,
                                relwidth = 1, relheight = 1)
        
        # 这是其tab页面,全部都是ttk.Frame.使用add是为了方便添加页面标签
        self.tab_play = ttk.Frame(None, style = 'wF.TFrame')
        self.tab_train = ttk.Frame(None, style = 'wF.TFrame')
        
        self.gui_notebook.add(self.tab_play, text = 'PLAY', padding = '0.05i')
        self.gui_notebook.add(self.tab_train, text = 'TRAIN', 
                              padding = '0.05i')
        
        self.player = MusicPlayer(self.tab_play, self.log)
        self.trainer = TrainGUI(self.tab_train, self.log)

class Log():
    """输出日志""" 
    def __init__(self, window):
        self.window = window
        
        self.massage = ''
        self.tag_active = 'norm'
        self.tags = {'norm': 'white', 'high': 'green', 'erro': 'red',
                     'warn': 'yellow'}
        
        self.set_log()
        self.get_time()
        
    def set_log(self):
        """设置左侧的日志"""
        self.log = ScrolledText(self.window, font = ('Cascadia', 10),
                                background = 'black')
        self.log.place(relx = 0.05, rely = 0.05, 
                       relwidth = 0.95, relheight = 0.95)
        # 设置标签颜色
        for tag in self.tags.keys():
            self.log.tag_config(tag, foreground = self.tags[tag])
        
        self.log.config(state = tk.DISABLED)
    
    def get_time(self):
        self.time1 = time.strftime('%A %b %d %Y')
        self.time2 = time.strftime('%H:%M:%S')
        self.clock = tk.Label(self.window, font = 5,
                              text = ' '.join((self.time1, self.time2)))
        self.clock.place(relx = 0.05, rely = 0.01)
        self.clock.after(1000, self.get_time)
    
    def log_print(self):
        self.log.config(state = tk.NORMAL)
        # 输出到log
        while self.massage != '':
            if self.massage[0] == '*':
                # 关键字匹配
                key = self.massage[1:5]
                self.massage = self.massage[5:]
                if key == 'star':
                    # 转义
                    self.log.insert(tk.END, '*', self.tag_active)
                elif key == 'time':
                    # 替换为当前时间
                    self.log.insert(tk.END, '[' + self.time2 + '] ', 
                                        self.tag_active)
                elif key in self.tags.keys():
                    self.tag_active = key
                
            else:
                self.log.insert(tk.END, self.massage[0],
                                    self.tag_active)
                self.massage = self.massage[1:]
                if self.massage == '':
                    self.log.see(tk.END)
        self.log.config(state = tk.DISABLED)
    
    def log_add(self, massage, show_time = False, end = ''):
        if show_time:
            self.massage += '*time'
        self.massage = self.massage + massage + end
        self.log_print()

if __name__ == '__main__':
    window = tk.Tk()
    
    main = MainDemoGui(window)
    
    window.mainloop()
    
    del main