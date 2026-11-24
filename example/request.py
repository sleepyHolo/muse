# -*- coding: utf-8 -*-

import os
import re
import time
import requests


"""
注意啦注意啦,这个爬虫只能从'https://freemidi.org/'爬mid文件
因为html解析是针对这个网站写的特化版本的正则表达式,没有解析html
"""

# your headers here
headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0'}

def get(text):
    pattern = '<a rel=nofollow id=downloadmidi class="btn btn-success btn-lg" title="[\(\)\s\w-]+" data-loading-text=loading... href=[\w-]+ download>Download MIDI</a>'
    if (re_match := re.search(pattern, text)):
        group = re_match.group()
    else:
        return ('', '')
    title = re.search('title="[\(\)\s\w-]+"', group).group().split('=')[1]
    title = ''.join(title.split())[1:-1]
    href = re.search('href=[\w-]+', group).group().split('=')[1]
    return (title, href)

def download(session, url, load_from, path_, index = ''):
    try:
        temp = session.get('/'.join((url, load_from)), headers = headers,
                           timeout = 5)
        title, herf = get(temp.text)
        if not title:
            return False
        
        temp = session.get('/'.join((url, herf)), headers = headers,
                           allow_redirects = False, stream = True,
                           timeout = (5, 20))
        with open(os.path.join(path_, f'{index}{title}.mid'), 'wb') as file:
            file.write(temp.content)
        print(f'Download file: {index}{title}.mid, from {herf}')
        return True
    except:
        print('Something wrong. Maybe timeout. ', end = '')
        return False
        

def download_files(session, from_, to, path_):
    url = 'https://freemidi.org'
    delta = to - from_
    fail = []
    for index in range(delta):
        print(f'[{index + 1}/{delta}]', end = ' ')
        if download(session, url, f'download4-{from_ + index}',
                    path_, index = f'{from_ + index}_') == False:
            print('Failed.')
            fail.append(f'https://freemidi.org/download4-{from_ + index}')
        time.sleep(1)   # 不清楚这个有没有必要,还是加上吧
    download_ok = delta - len(fail)
    print(f'\ndownloaded {download_ok}/{delta}.')
    return fail

if __name__ == '__main__':
    session = requests.Session()
    # your path here
    path_ = 'D:/download_midi/'
    
    if not os.path.exists(path_):
        os.mkdir(path_)
    
    from_ = 1000
    to = 1005
    fail = download_files(session, from_, to, path_)
    
    # 失败文件log,不必要
    try:
        name = f'fail_log_{int(time.time())}.txt'
        with open(os.path.join(path_, name), 'wb') as file:
            file.write('\n'.join(fail).encode(encoding = 'utf-8'))
        print(f'Log: {name}')
    except Exception:
        print('No failed files log.')