# -*- coding: utf-8 -*-

from distutils.core import setup, Extension

module = Extension('_muse', sources = ['muse_wrap.cxx'])

setup(name = 'muse',
      version = '0.2',
      author = 'HXW',
      description = """提供简单的MIDI输出控件类""",
      ext_modules = [module],
      py_modules = ['muse'])

#print('done')