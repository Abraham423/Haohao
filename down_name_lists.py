"""
Specially designed to download IMDB stars， totally about 600 Million peoples
"""
import requests
import os
import re
from tqdm import tqdm
import numpy as np
import json
from time import time
import scrapy
from bs4 import BeautifulSoup

#import douban
#from douban import items #import DoubanItem
from scrapy import Selector
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

def getNamelistFromBS(bs):
    # tic = time()
    name_tags = bs.find_all("h3")
    name_lists = []
    for i, h3 in enumerate(name_tags):
        if len(h3.contents) < 2:
            continue
        star_name = h3.contents[-2].string.strip()
        name_lists.append(star_name)
    # toc=time()
    # print('%.6f' % (toc-tic))
    return name_lists


def getNextPageUrl(bs):
    base_url = 'https://www.imdb.com'
    next_page_tag = bs.select('.lister-page-next')[0]
    next_page_link = next_page_tag.attrs['href']
    next_page_url = base_url + next_page_link
    # print(next_page_url)
    return next_page_url


def write_txt(base_dir, idx, contents):
    fp = os.path.join(base_dir, 'file{}.txt'.format(idx))
    f = open(fp, 'w')
    for cont in contents:
        f.writelines(cont + ";")
    f.close()


def run_30000_pages(url_dir=None):
    base_dir = 'imdb_name_lists'
    if not os.path.exists(base_dir):
        os.mkdir(base_dir)

    url_fp = os.path.join(base_dir, 'urls.txt')
    if url_dir is None:
        f = open(url_fp,'r')
        lines = [l.strip() for l in f.readlines()]
        idx_start = len(lines)
        url_dir = lines[-1]

    else:
        idx_start = 0
    print('starting from {}, the {}th urls'.format(url_dir,idx_start))
    url_file = open(url_fp, 'a')
    for i in tqdm(range(idx_start,idx_start+300000)):
        response = requests.get(url_dir,timeout=10)
        web_content = response.content
        bs = BeautifulSoup(web_content, 'html.parser')
        url_dir = getNextPageUrl(bs)
        names = getNamelistFromBS(bs)
        write_txt(base_dir, i, names)
        url_file.writelines(url_dir + "\n")
        url_file.flush()

if __name__ == "__main__":
    url_dir = 'https://www.imdb.com/search/name/?gender=male%2Cfemale&ref_=nvcelm'
    while True:
        try:
            run_30000_pages(url_dir=None)
        except Exception as e:
            print(e)







