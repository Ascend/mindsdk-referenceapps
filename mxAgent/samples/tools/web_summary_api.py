# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.


import asyncio
import os
import re
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, wait, as_completed

import aiohttp
import requests
import tiktoken
import urllib3
from bs4 import BeautifulSoup
from loguru import logger
from samples.tools.duck_search import call_duck_duck_go_search


def check_number_input(num, crow):
    if not num.isdigit():
        return False
    num = int(num)
    if num > crow:
        return False
    return True


async def bai_du(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '\
               Chrome/126.0.0.0 Safari/537.36"
    }
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False, limit=25), trust_env=True,
                                     headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as session:
        async with session.get(url) as response:
            res = await response.text()
            return res


class WebSummary:
    encoder = tiktoken.get_encoding("gpt2")

    @classmethod
    def get_detail_copy(cls, url, summary_prompt):
        os.environ['CURL_CA_BUNDLE'] = ''  # 关闭SSL证书验证
        urllib3.disable_warnings()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '\
               Chrome/126.0.0.0 Safari/537.36"
        }
        try:
            mommt = datetime.now(tz=timezone.utc)
            logger.info(f"start request website: {mommt.strftime('%Y-%m-%d %H:%M:%S')},{url}")
            response = requests.get(
                url, headers=headers, timeout=(3, 3), stream=True)
            mommt = datetime.now(tz=timezone.utc)
            logger.info(f"finish request website: {mommt.strftime('%Y-%m-%d %H:%M:%S')},{url}")
            if response.status_code != 200:
                logger.error(f"获取网页{url}内容失败")
                return '', f"获取网页{url}内容失败"

            content = response.content
            bsobj = BeautifulSoup(content, 'html.parser')
            txt = bsobj.get_text()
            text = re.sub(r'\n{2,}', '\n', txt).replace(' ', '')
            text = re.sub(r'\n{2,}', '\n', text)
        except Exception as e:
            logger.error(e)
            return '', e
        res = cls.generate_content(text, summary_prompt)
        mommt = datetime.now(tz=timezone.utc)
        logger.info(f"finish summary website: {mommt.strftime('%Y-%m-%d %H:%M:%S')},{url}")
        return res, None

    @classmethod
    async def get_details(cls, url, summary_prompt):
        os.environ['CURL_CA_BUNDLE'] = ''
        urllib3.disable_warnings()
        try:
            mommt = datetime.now(tz=timezone.utc)
            logger.info(f"start request website: {mommt.strftime('%Y-%m-%d %H:%M:%S')},{url}")
            response = await bai_du(url)
            mommt = datetime.now(tz=timezone.utc)
            logger.debug(f"finish request website: {mommt.strftime('%Y-%m-%d %H:%M:%S')},{url}")
            content = response
            bsobj = BeautifulSoup(content, 'html.parser')
            txt = bsobj.get_text()
            text = re.sub(r'\n{2,}', '\n', txt).replace(' ', '')
            text = re.sub(r'\n{2,}', '\n', text)
            if 'PleaseenableJSanddisableanyadblocker' in text:
                text = ""
        except Exception as e:
            logger.error(e)
            return '', e
        if len(text) == 0:
            return "", "no valid website content"
        res = cls.generate_content(text, summary_prompt)
        mommt = datetime.now(tz=timezone.utc)
        logger.info(f"finish summary website: {mommt.strftime('%Y-%m-%d %H:%M:%S')},{url}")
        return res, None

    @classmethod
    def summary_call(cls, web, max_summary_number, summary_prompt):
        title = web.get("title", "")
        url = web.get("href")
        snippet = web.get("body", "")
        web_summary = {}
        if url is None:
            return web_summary

        web_summary['title'] = title
        web_summary['url'] = url
        try:
            content, err = asyncio.run(cls.get_details(url, summary_prompt))
        except Exception as e:
            logger.error(e)
        if not isinstance(content, str) or len(content) == 0:
            web_summary['snippet'] = snippet
        else:
            web_summary['content'] = content

        return web_summary

    @classmethod
    def web_summary(cls, keys, search_num, summary_num, summary_prompt, llm):
        logger.add('app.log', level='DEBUG')
        cls.llm = llm
        try:
            mommt = datetime.now(tz=timezone.utc)
            logger.debug(f"start duck duck go search: {mommt.strftime('%Y-%m-%d %H:%M:%S')}")
            if isinstance(keys, list):
                keys = ",".join(keys)
            search_result = call_duck_duck_go_search(keys, search_num)
            mommt = datetime.now(tz=timezone.utc)
            logger.debug(f"finish duck duck go search: {mommt.strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            logger.error(e)
            return []

        max_summary_number = summary_num

        webs = []
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            for web in search_result:
                thread = executor.submit(
                    cls.summary_call, web, max_summary_number, summary_prompt)
                futures.append(thread)
            for future in as_completed(futures):
                webs.append(future.result())
            wait(futures)
        return webs

    @classmethod
    def build_summary_prompt(cls, query, prompt):
        max_input_token_num = 4096
        if len(query) == 0:
            return prompt.format(text=query)
        input_token_len = len(WebSummary.encoder.encode(query))
        prompt_len = len(WebSummary.encoder.encode(prompt))
        clip_text_index = int(
            len(query) * (max_input_token_num - prompt_len) / input_token_len)
        clip_text = query[:clip_text_index]
        return prompt.format(input=clip_text)

    @classmethod
    def generate_content(cls, query, prompt):
        max_tokens = 1000
        try:
            pmt = WebSummary.build_summary_prompt(query, prompt)
            output = cls.llm(prompt=pmt, max_tokens=max_tokens)
        except Exception as e:
            logger.error(e)
            return e
        return output
