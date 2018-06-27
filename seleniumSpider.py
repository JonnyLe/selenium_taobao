# encoding=utf-8

__author__ = 'Jonny'
__location__ = '西安'
__date__ = '2018-05-14'

'''
需要的基本开发库文件：
requests,pymongo,pyquery,selenium
开发流程：
    搜索关键字：利用selenium驱动浏览器搜索关键字，得到查询后的商品列表
    分析页码并翻页：得到商品页码数，模拟翻页，得到后续页面的商品列表
    分析提取商品内容：利用PyQuery分析页面源代码，解析获得商品列表信息
    存储到MongDB中：将商品的信息列表存储到数据库MongoDB。
'''
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from pyquery import PyQuery as pq
import pymongo
import re
import settings
import time


# browser = webdriver.Chrome()
browser = webdriver.PhantomJS()
wait = WebDriverWait(browser,10)
client = pymongo.MongoClient('localhost',27017)
mongo = client['taobao']

def searcher(keyword):
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    print('大家注意啦！！！爬虫开始啦！')
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    url =  'https://www.taobao.com/'
    browser.get(url=url)
    try:
        #判断页面加载是够成功，设置等待时间
        #判断位置1：搜索输入框是否加载完成
        input_kw = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#q'))
        )
        #判断位置2：搜索输入框对应的搜索按键是否加载完成
        submit = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR,'#J_TSearchForm > div.search-button > button'))
        )
        input_kw.send_keys(keyword)
        submit.click()
        #等待页面加载完成，便于准确判断网页的总页数
        page_counts = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > div.total'))
        )
        parse_page()
        return page_counts.text

    except TimeoutException as e:
        print(e.args)
        return searcher(keyword)


#实现翻页
def next_page(page_number):
    try:
        # 判断页面加载是够成功，设置等待时间
        # 判断位置1：页面跳转输入页是否加载完成
        input_page = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > input'))
        )
        # 判断位置2：确认按键是否加载完成
        submit = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit'))
        )
        input_page.send_keys(page_number)
        print('``````````````````````````````````````````````````````````````````````````')
        print('要翻页啦！！！页数：',page_number)
        print('``````````````````````````````````````````````````````````````````````````')
        submit.click()
        #判断翻页是否成功
        wait.until(EC.text_to_be_present_in_element(
            (By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > ul > li.item.active'),str(page_number))
        )
        parse_page()
    except TimeoutException as e:
        print(e.args)
        next_page(page_number)


#对页面进行数据处理
def parse_page():
    # wait.until(EC.presence_of_element_located(By.CSS_SELECTOR,'#mainsrp-itemlist > div > div'))
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-itemlist .items .item')))
    html = browser.page_source
    doc = pq(html)
    items = doc('#mainsrp-itemlist .items .item').items()
    for item in items:
        goods = {
            'image':item.find('.pic .img').attr('src'),
            'price':item.find('.price').text(),
            'deal':item.find('.deal-cnt').text()[:-3],
            'title':item.find('.title').text(),
            'shop':item.find('.shop').text(),
            'location':item.find('.location').text()
        }
        print(goods)
        data_storage(goods)


#将数据存入数据库
def data_storage(goods):
    try:
        if mongo['mongo_sheet'].insert(goods):
            print('Successfully storage!')
    except Exception as e:
        print('failedly storage!',goods)



def main(keyword):
    text = searcher(keyword)
    print(text)
    #获取总页数
    pages = int(re.compile('(\d+)').search(text).group(0))
    print(pages)
    for i in range(2,pages+1):
        next_page(i)
    browser.close()


if __name__ == '__main__':
    keyword = input('请输入要查询的关键字：')
    main(keyword)