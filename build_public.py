# -*- coding: utf-8 -*-
"""从主项目复制一份「公开单机版」到本仓库。

为什么需要这一步：主项目将来会接真正的云同步（账号 + 后端 + 冲突规则）。
公开仓库里的这份必须永远是**零云端**的 —— 打开不需要登录、不向任何服务器
发送一个字节。所以每次主项目发版后跑一遍本脚本，而不是手工复制。

用法（在仓库根目录）：
    python build_public.py <主项目的 app 目录>
    # 也可以用环境变量
    HB_APP_SRC=<主项目的 app 目录> python build_public.py

本脚本做的事：
  1. 复制会公开的文件：index.html / sw.js / manifest.webmanifest / fonts/ / icons/
  2. 把设置页「云同步」那栏改成单机版说明（这一栏点不动，也不会发请求）
  3. 自检：一律用"像不像单机版"的断言，不写死任何域名或路径
       - 页面里不许有 fetch( / XMLHttpRequest / WebSocket
       - 不许有 http(s):// 外链（SVG 的 xmlns 除外）
       - 不许出现本机绝对路径
  4. 任何一步对不上就 sys.exit(1) —— 宁可发不出去，也不要静默发出一份带云端代码的页面

脚本里刻意不含任何真实地址、密钥、本机路径：它自己也会被公开。
"""
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

COPY = ['index.html', 'sw.js', 'manifest.webmanifest', 'fonts', 'icons']

# 「云同步」那一栏在公开版里的说法。写死成"单机版"，不写"以后会有"——
# 公开仓库的读者不该看到一个点不动的待办事项。
SYNC_PILL_OLD = '<span class="pill">未开启</span>'
SYNC_PILL_NEW = '<span class="pill">单机版</span>'
SYNC_TEXT_RE = re.compile(r'<div class="rowtxt">现在只存在这台手机里。[^<]*</div>')
SYNC_TEXT_NEW = ('<div class="rowtxt">这一份是公开的单机版：记录只存在你自己的浏览器里，'
                 '不向任何服务器发送数据。想要多端同步，得自己接一个后端。</div>')

ALLOWED_URL = re.compile(r'xmlns(:\w+)?="http://www\.w3\.org/')
ANY_URL = re.compile(r'https?://')
LOCAL_PATH = re.compile(r'[A-Za-z]:[\\/]{1,2}Users[\\/]|/Users/[^/\s]+/|/home/[^/\s]+/')
NETWORK = re.compile(r'\bfetch\s*\(|XMLHttpRequest|new\s+WebSocket|navigator\.sendBeacon')

problems = []


def note(msg):
    print(msg)


def main():
    if len(sys.argv) > 1:
        src = sys.argv[1]
    else:
        src = os.environ.get('HB_APP_SRC', '')
    if not src:
        sys.exit('用法: python build_public.py <主项目的 app 目录>（或设 HB_APP_SRC）')
    src = os.path.abspath(src)
    if not os.path.isfile(os.path.join(src, 'index.html')):
        sys.exit('在 %s 里找不到 index.html' % src)

    # 1. 复制（先删后拷，避免旧文件残留）
    for name in COPY:
        dst = os.path.join(HERE, name)
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        elif os.path.exists(dst):
            os.remove(dst)
        s = os.path.join(src, name)
        if os.path.isdir(s):
            shutil.copytree(s, dst)
        elif os.path.isfile(s):
            shutil.copy2(s, dst)
        else:
            problems.append('源目录缺少 %s' % name)
    note('已复制: ' + ', '.join(COPY))

    # 2. 改云同步那一栏
    p = os.path.join(HERE, 'index.html')
    with open(p, encoding='utf-8') as f:
        s = f.read()

    if SYNC_PILL_NEW in s:
        note('云同步 pill 已是公开版的写法')
    elif s.count(SYNC_PILL_OLD) == 1:
        s = s.replace(SYNC_PILL_OLD, SYNC_PILL_NEW)
        note('云同步 pill: 未开启 → 单机版')
    else:
        problems.append('云同步 pill 没找到（出现 %d 次，期望 1）：主项目的设置页是不是改过？'
                        % s.count(SYNC_PILL_OLD))

    if SYNC_TEXT_NEW in s:
        note('云同步说明已是公开版的写法')
    elif len(SYNC_TEXT_RE.findall(s)) == 1:
        s = SYNC_TEXT_RE.sub(SYNC_TEXT_NEW, s)
        note('云同步说明: 已改成单机版口径')
    else:
        problems.append('云同步说明没找到（匹配 %d 处，期望 1）' % len(SYNC_TEXT_RE.findall(s)))

    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(s)

    # 3. 自检：断言"像单机版"，而不是"不含某个具体域名"
    for name in ('index.html', 'sw.js', 'manifest.webmanifest'):
        path = os.path.join(HERE, name)
        with open(path, encoding='utf-8') as f:
            t = f.read()
        if name != 'sw.js' and NETWORK.search(t):
            problems.append('%s 里出现了网络调用（%s）' % (name, NETWORK.search(t).group(0)))
        stripped = ALLOWED_URL.sub('', t)
        if ANY_URL.search(stripped):
            problems.append('%s 里出现了外链: %s' % (name, ANY_URL.search(stripped).group(0)))
        if LOCAL_PATH.search(t):
            problems.append('%s 里出现了本机路径: %s' % (name, LOCAL_PATH.search(t).group(0)))
    note('自检: 无网络调用 / 无外链 / 无本机路径')

    if problems:
        print('\n构建失败：')
        for x in problems:
            print('  ! ' + x)
        sys.exit(1)
    print('\n完成。可以提交了。')


if __name__ == '__main__':
    main()
