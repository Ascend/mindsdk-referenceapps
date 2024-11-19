# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

import re

from bs4 import BeautifulSoup
from loguru import logger
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

CHROME_DRIVER_PATH = '/usr/local/share/chromedriver/chromedriver'
GOOGLE_URL = 'https://www.google.com/'


def google_search(keywords, max_number=3):
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('start-maximized')
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument('--disable-browser-side-navigation')
    chrome_options.add_argument('enable-automation')
    chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument('enable-features=NetworkServiceInProcess')
    driver = webdriver.Chrome(
        executable_path=CHROME_DRIVER_PATH, options=chrome_options)
    try:
        driver.get(GOOGLE_URL)
        WebDriverWait(driver, 5).until(
            expected_conditions.presence_of_element_located((By.NAME, 'q')))
        box = driver.find_element(By.NAME, 'q')
        box.send_keys(keywords)
        box.send_keys(Keys.RETURN)
        WebDriverWait(driver, 5).until(
            expected_conditions.title_contains(keywords))
        bsobj = BeautifulSoup(driver.page_source, 'html.parser')
        elements = bsobj.find_all('div', {'class': re.compile('MjjYud')})
        search_res = []
        for element in elements:
            if element.a and element.a.h3:
                link = element.a['href']
                title = element.a.h3.text.strip()
            else:
                continue
            high_light = element.find('em', {'class': re.compile('t55VCb')})
            if high_light is None:
                continue
            parent = high_light.parent
            res = {
                "snippet": parent.text.strip(),
                "title": title.strip(),
                "url": link.strip()
            }
            search_res.append(res)
            if len(search_res) >= max_number:  # 收集指定数量的网页
                break
        return search_res
    except TimeoutError as e:
        logger.error(f"timeout: {e}")
    finally:
        driver.quit()
    return search_res
