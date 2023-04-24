import os
import sys
import time
import json
import platform
from urllib.parse import urlparse
from base64 import b64encode, b64decode
from http.client import HTTPConnection
from http.client import HTTPSConnection

import tty
import termios


def install_module(module_name):
    print('尝试安装模块{0}'.format(module_name))
    cmd = '"{0}" -m pip install {1}'.format(sys.executable, module_name)
    print('执行命令：{0}'.format(cmd))
    ret = os.system(cmd)
    if ret != 0:
        print('{0} 安装失败了，请手动安装！（小声哔哔：你是不是开了代理）！'.format(module_name))
        sys.exit(0)


def check_iterm2():
    fd = sys.stdin.fileno()
    old_attributes = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        new_attributes = termios.tcgetattr(fd)
        new_attributes[3] = new_attributes[3] & ~termios.ICANON & ~termios.ECHO
        termios.tcsetattr(fd, termios.TCSANOW, new_attributes)

        sys.stdout.write("\033[1337n")
        sys.stdout.write("\033[5n")
        sys.stdout.flush()

        response = read_terminal_response("n")
        if response.startswith("ITERM2"):
            return True
    finally:
        termios.tcsetattr(fd, termios.TCSANOW, old_attributes)
    return False


def read_terminal_response(terminator: str) -> str:
    sys.stdin.read(1)
    sys.stdin.read(1)
    result = ""
    while True:
        sys.stdout.flush()
        ch = sys.stdin.read(1)
        if ch == terminator:
            break
        result += ch
    return result


def show_image(img_data):
    img_code_tmpl = "\033]1337;File=inline=1;width={}px;height={}px;:{}\007"
    print(
        img_code_tmpl.format(
            200,
            40,
            b64encode(img_data).decode("ascii")
        )
    )


# TODO 自动分析返回包json，找到图片数据的位置
# def find_image_data_in_dict(res_data):
#     '''
#     返回编码类型和数据在字典中的索引路径
#     '''
#     if instance(res_data, str):
#         if res_data.startswith("data:image/jpeg"):
#             return "image/jpeg"
#         elif res_data.startswith("data:image/png"):
#             return "image/png"
#         else:
#             return None
#     elif instance(res_data, list):
#         for i in range(len(res_data)):

#     elif instance(res_data, dict):
#         pass
#     else:
#         return None



try:
    import ddddocr
except (ImportError, ModuleNotFoundError):
    install_module("ddddocr")
    import ddddocr


def main():
    # print(os.getcwd())
    isIterm2 = check_iterm2()
    for root, ds, fs in os.walk(os.getcwd(), topdown=True):
        if root != os.getcwd():
            break
        for f in fs:
            if os.path.splitext(f)[1] == ".png":
                os.remove(f)

    verification_code_url = sys.argv[1].strip()
    print(verification_code_url)
    verification_code_url_up = urlparse(verification_code_url)
    if verification_code_url_up.scheme == "https":
        conn = HTTPSConnection(verification_code_url_up.netloc)
    else:
        conn = HTTPConnection(verification_code_url_up.netloc)
    
    conn.request("GET", verification_code_url_up.path + "?" + verification_code_url_up.query)
    res = conn.getresponse() 
    # print(res)
    res_content_type = res.getheader("Content-Type")
    if res_content_type == "application/json":
        res_json = res.read().decode()
        # print(res_json)
        try:
            res_data = json.loads(res_json)
        except Exception as e:
            print("解析返回结果失败！", e)
            sys.exit(1)
        print(json.dumps(res_data, indent=4))
        index_path = input("输入索引路径（例如：data>0>img）：")
        index_path_list = index_path.split(">")

    # sys.exit(0)
    
    # 实例化DDDDOCR
    ocr = ddddocr.DdddOcr(show_ad=False)

    for i in range(6):
        print("-"*20)
        print("【{0}】".format(i+1))
        conn.request("GET", verification_code_url_up.path + "?" + verification_code_url_up.query)
        res = conn.getresponse()
        if res_content_type == "application/json":
            res_json = res.read().decode()
            # print(res_json)
            try:
                res_data = json.loads(res_json)
            except Exception as e:
                print("解析返回结果失败！", e)
                sys.exit(1)
            # print(json.dumps(res_data, indent=4))
            _tmp_data = res_data
            for i in index_path_list:
                if i.isdigit():
                    i = int(i)
                    _tmp_data = _tmp_data[i]
                else:
                    _tmp_data = _tmp_data[i]
            if _tmp_data and "base64," in _tmp_data:
                verification_code_b64_str = _tmp_data.split("base64,")[1]
            else:
                print("未找到数据！")
                sys.exit(1)
            verification_code_res_data = b64decode(verification_code_b64_str)
        
        else:
            verification_code_res_data = res.read()

        if isIterm2:
            show_image(verification_code_res_data)

        # print("开始识别")
        start_time = time.time()
        verification_code_str = ocr.classification(verification_code_res_data)
        end_time = time.time()
        print("识别完成，耗时：{0} 秒".format(end_time - start_time))
        print(verification_code_str)

        with open(verification_code_str + ".png", "wb") as f:
            f.write(verification_code_res_data)
        print("-"*20)


if __name__ == "__main__":
    main()
    
    