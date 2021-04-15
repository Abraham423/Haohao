"""
@auther : wanghao
@data : 2021/04/15
@description : To download from google image search
"""
import requests
import os
import shutil
import re
from tqdm import tqdm
import numpy as np
import json
from time import time
import scrapy
from bs4 import BeautifulSoup
import argparse
#import douban
#from douban import items #import DoubanItem
# from scrapy import Selector
# from selenium import webdriver
# from webdriver_manager.chrome import ChromeDriverManager
from multiprocessing import Pool
from threading import Thread

parser = argparse.ArgumentParser()
parser.add_argument("--processes",type=int,default=10,help='how many processes you want')
parser.add_argument("--namelist_dir",type=str,default="imdb_name_lists",help='')
parser.add_argument("--namelist_save_dir",type=str,default="imdb_name_lists_finished",help='')
parser.add_argument("--image_save_dir",type=str,default="IMDBImages",help='')
parser.add_argument("--blackname_file",type=str,default="blackname_file.txt",help='')

# filename, file_dir='imdb_name_lists', save_dir='imdb_name_lists_finished',
#                                data_save_dir="IMDBImages"
args = parser.parse_args()
black_name_file = open(args.blackname_file,'a')

def getUrlsFromKeyword(keyword="michael jackson"):
    question = keyword.replace(' ', '+')
    url_dir = f"https://google.com/search?q={question}&tbm=isch&sclient=img"
    # 找到合适的代理
    # desktop user-agent
    url_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:65.0) Gecko/20100101 Firefox/65.0"
    # mobile user-agent
    mobile_user_agent = "Mozilla/5.0 (Linux; Android 7.0; SM-G930V Build/NRD90M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.125 Mobile Safari/537.36"

    headers = {"user-agent": mobile_user_agent}
    resp = requests.get(url_dir, headers=headers,timeout=60)
    if resp.status_code == 200:
        soup = BeautifulSoup(resp.content, "html.parser")
        tags = soup.find_all(attrs={"class": "rg_i Q4LuWd"})
        # get all urls
        img_urls = []
        for tag in tags:
            if 'data-src' in tag.attrs:
                img_url = tag.attrs['data-src']
                img_urls.append(img_url)
        return img_urls
    else:
        print(f'{url_dir} not found !')
        return []


def downImages(keyword, urls, save_dir="IMDBImages"):
    keyword = keyword.replace(' ', '_')
    save_dir = os.path.join(save_dir, keyword)
    url_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:65.0) Gecko/20100101 Firefox/65.0"
    # mobile user-agent
    mobile_user_agent = "Mozilla/5.0 (Linux; Android 7.0; SM-G930V Build/NRD90M) AppleWebKit/537.36 (KHTML, like Gecko)\
    Chrome/59.0.3071.125 Mobile Safari/537.36"
    headers = {"user-agent": mobile_user_agent}
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)
    tic = 0
    for i, url in enumerate(urls):
        try:
            ip = os.path.join(save_dir, f'img_{i}.jpg')
            raw_img = requests.get(url=url, headers=headers,timeout=10).content
            with open(ip, 'wb') as f:
                f.write(raw_img)
                f.close()
        except:
            tic += 1
            continue
    if tic:
        print(f"{save_dir} totally missed {tic}/{len(urls)} images ! ")
    if tic/len(urls) > 0.4:
        black_name_file.writelines(keyword+"\n")
        black_name_file.flush()

def downImagesFromNamelistFile(filename, file_dir='imdb_name_lists', save_dir='imdb_name_lists_finished',
                               data_save_dir="IMDBImages"):
    filepath = os.path.join(file_dir, filename)
    new_filename = filename[:-4] + '_unfinished.txt'
    new_filepath = os.path.join(save_dir, new_filename)
    f = open(filepath, 'r')
    namelist = [x for x in f.read().strip().split(';')]
    f.close()
    # print("Namelist : \n", namelist)

    new_file_exists = os.path.exists(new_filepath)
    f = open(new_filepath, 'a')
    namelist_exists = []
    if new_file_exists and f.readable():
        namelist_exists = [x for x in f.read().strip().split(';')]
    for i, keyword in enumerate(namelist):
        if keyword in namelist_exists:
            continue
        urls = getUrlsFromKeyword(keyword)
        downImages(keyword, urls, data_save_dir)
        f.writelines(keyword + ";")
        f.flush()
    f.close()
    new_filepath_rename = new_filepath.replace("unfinished", "finished")
    shutil.move(new_filepath, new_filepath_rename)

def runInLoop(filenames, file_dir='imdb_name_lists', save_dir='imdb_name_lists_finished',
                               data_save_dir="IMDBImages"):
    for filename in tqdm(filenames):
        downImagesFromNamelistFile(filename, file_dir, save_dir,
                               data_save_dir)



if __name__ == "__main__":
    # parser.add_argument("--namelist_dir", type=str, default="imdb_name_lists", help='')
    # parser.add_argument("--namelist_save_dir", type=str, default="imdb_name_lists_finished", help='')
    # parser.add_argument("--image_save_dir", type=str, default="IMDBImages", help='')

    # filename, file_dir='imdb_name_lists', save_dir='imdb_name_lists_finished',
    #                                data_save_dir="IMDBImages"
    namelist_file_names = os.listdir(args.namelist_dir)
    namelist_file_names_to_down = []
    namelist_file_names_saved = os.listdir(args.namelist_save_dir)

    print('Passing over namelist files that have been downloaded')
    for x in tqdm(namelist_file_names):
        x1 = x.replace(".txt","_finished.txt")
        if not x1 in namelist_file_names_saved:
            namelist_file_names_to_down.append(x)
    print('Leaving %d files to download ' % len(namelist_file_names_to_down))
    # downImagesFromNamelistFile(namelist_file_names_to_down[0], args.namelist_dir, args.namelist_save_dir,
    #                                     args.image_save_dir)
    indexs = np.linspace(0,len(namelist_file_names_to_down),args.processes).astype(np.int64)
    threads = []
    for i in range(len(indexs)-1):
        start_idx = indexs[i]
        end_idx = indexs[i+1]
        t=Thread(target=runInLoop,args=(namelist_file_names_to_down[start_idx:end_idx],args.namelist_dir, args.namelist_save_dir,
                               args.image_save_dir))
        t.start()
        threads.append(t)
    for t in threads:
        if t is not None:
            t.join()

    # process_pool = Pool(processes=args.processes)
    # for namelist_file_name in tqdm(namelist_file_names_to_down):
    #     process_pool.apply_async(downImagesFromNamelistFile, args=(namelist_file_name,args.namelist_dir, args.namelist_save_dir,
    #                            args.image_save_dir))
    # process_pool.close()
    # process_pool.join()

































