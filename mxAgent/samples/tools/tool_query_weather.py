# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

import datetime
import json
import json
import os
from zoneinfo import ZoneInfo

import requests
import urllib3
from agent_sdk.toolmngt.api import API
from agent_sdk.toolmngt.tool_manager import ToolManager
from loguru import logger

AMAP_API_KEY = "75bcb2edf5800884a31172dd0d970369"
WEEK_MAP = {
    0: "Monday",
    1: "Tuesday",
    2: "Wednesday",
    3: "Thursday",
    4: "Friday",
    5: "Saturday",
    6: "Sunday"
}
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '\
        Chrome/126.0.0.0 Safari/537.36"
}


@ToolManager.register_tool()
class QueryWeather(API):
    name = "QueryWeather"
    description = "This API is used to query weather forecast from the network according to the user's input question,"
    weekday = WEEK_MAP.get(datetime.datetime.now(ZoneInfo("Asia/Shanghai")).weekday(), '')
    input_parameters = {

        'destination_city': {'type': 'str', 'description': 'the destination city user aim to query weather.'},
        "province": {'type': 'str', 'description': 'The province corresponding to the city'},
        "date": {'type': 'str', 
                 'description':("The date of the user want to query, today is"+
                                f"{datetime.date.today()}, and today is {weekday}, "+
                                "please reason the date from user's query, and format with YYYY-MM-DD,")
                },
        'requirement': {'type': 'str', 'description': 'The more requirement of weather mentioned by the user'},
    }
    output_parameters = {
        "forecast": {'type': 'str',
                     'description': 'the weather forecast information'},
    }

    example = (
        """
        {
            "destination_city": "ShenZhen",
            "province": "GuangDong",
            "date": "2022-10-01"
        }
        """)

    def __init__(self, ):
        os.environ['CURL_CA_BUNDLE'] = ''  # 关闭SSL证书验证
        urllib3.disable_warnings()

    def get_forecast(self, url, param, city=""):
        headers = REQUEST_HEADERS
        response = requests.get(url, params=param, headers=headers, timeout=5)
        if response.status_code != 200:
            logger.error(f"获取网页{url}内容失败")
            raise Exception(f"获取网页{url}内容失败")
        content = response.content
        text = json.loads(content)
        return text.get("data")

    def get_city2province(self, url, city):
        headers = REQUEST_HEADERS
        params = {
            "city": city,
            "source": "pc"
        }
        response = requests.get(url, params=params, headers=headers, timeout=5)
        if response.status_code != 200:
            logger.error(f"获取网页{url}内容失败")
            raise Exception(f"获取网页{url}内容失败")
        content = response.content
        text = json.loads(content)
        return text.get("data")

    def format_weather(self, weekly_weather):
        # 精简输入
        key_keeps = [
            'day_weather', 'day_wind_direction', 'day_wind_power',
            'max_degree', 'min_degree', 'night_weather', 'night_wind_direction', 'night_wind_power'
        ]
        summary_copy = []
        for key, info in weekly_weather.items():
            time = info.get('time', key)
            daily = {}
            if isinstance(info, dict):
                info_keeps = {k: info[k] for k in key_keeps if k in info}
            daily[time] = info_keeps
            summary_copy.append(daily)
        return summary_copy

    def format_request_param(self, data, weather_type):
        for key, value in data.items():
            city2province = value.replace(" ", "").split(",")
            data[key] = city2province
        # 遇到城市同名，认为是市的概率大于县
        _, max_probablity = min(data.items(), key=lambda item: len(item[1]))
        if len(max_probablity) >= 2:
            province = max_probablity[0]
            city = max_probablity[1]
            country = max_probablity[2] if len(max_probablity) >= 3 else ""
        params = {
            "source": "pc",  # 请求来源，可以填 pc 即来自PC端
            "province": province,  # 省，
            "city": city,  # 市，
            "country": country,  # 县区
            "weather_type": weather_type
        }
        return params

    def call(self, input_parameter, **kwargs):
        des = input_parameter.get('destination_city')
        departure_date = input_parameter.get("date")
        weather_type = "forecast_24h"

        try:
            if des is None:
                return self.make_response(input_parameter, results="", success=False, exception="")
            try:
                data = self.get_city2province("https://wis.qq.com/city/like", des)
            except Exception as e:
                e = str(e)
                return self.make_response(input_parameter, results=e, success=False, exception=e)
            if len(data) == 0:
                return self.make_response(input_parameter,
                                          results="未能找到所查询城市所在的省份或市", success=False, exception="")

            params = self.format_request_param(data, weather_type)
            try:
                forecast = self.get_forecast(
                    "https://wis.qq.com/weather/common", params)
            except Exception as e:
                e = str(e)
                return self.make_response(input_parameter, results=e, success=False, exception=e)
            weekly_weather = forecast.get(weather_type)
            summary_copy = self.format_weather(weekly_weather)
            if departure_date is None:
                res = {
                    'forecast': summary_copy
                }
                return self.make_response(input_parameter, results=res, exception="")

            try:
                formated_departure = datetime.datetime.strptime(
                    departure_date, "%Y-%m-%d").date()
            except ValueError as e:
                logger.warning(e)
                formated_departure = datetime.date.today()
            gaps = (formated_departure - datetime.date.today()).days
            weather_summary = summary_copy[gaps + 1:]

            if len(weather_summary) == 0:
                weather_summary = "**抱歉，我最多只能查询最近7天的天气情况，例如下面是我将为你提供最近的天气预报**:\n" + \
                                  json.dumps(summary_copy, ensure_ascii=False)
            res = {
                'forecast': weather_summary
            }
        except Exception as e:
            logger.error(e)
            e = str(e)
            return self.make_response(input_parameter, results=e,
                                      success=False, exception=e)
        else:
            return self.make_response(input_parameter, results=res, exception="")
