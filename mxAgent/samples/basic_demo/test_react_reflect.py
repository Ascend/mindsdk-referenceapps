# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.

import warnings
import argparse
import os

from loguru import logger

from agent_sdk.agentchain.react_agent import ReactReflectAgent
from agent_sdk.llms.llm import get_llm_backend, BACKEND_OPENAI_COMPATIBLE
from samples.tools import QueryAccommodations, QueryAttractions, \
    QueryGoogleDistanceMatrix, QueryTransports, Finish

warnings.filterwarnings('ignore')

MAX_CONTEXT_LEN = 4096


EXAMPLE = '''
Question: Can you help with a 5 day trip from Orlando to New York? Departure date is March 10, 2022.
Thought: To create a travel itinerary, I need to find accommodations, transportation, and attractions in New York. I will first find hotels in New York.
Action: QueryAccommodations
Action Input: {"destination_city": "New York", "position": "Central Park", "rank": "four stars"}
Observation1: [{"title": "紐約市10 大最佳四星級酒店 - Tripadvisor", "url": "https://www.tripadvisor.com.hk/Hotels-g60763-zfc4-New_York_City_New_York-Hotels.html", "snippet": "紐約市四星級酒店 · 1. Moxy NYC Times Square · 3,825 則評論 · 2. 格甚溫酒店 · 1,155 則評論 · 3. 托米哈德森廣場飯店 · 3,277 則評論 · 4. 時代廣場愛迪生酒店 · 5. Hard ..."}, {"title": "中央公園酒店| 人氣優惠及套餐", "url": "https://www.agoda.com/zh-hk/park-central-hotel/hotel/new-york-ny-us.html", "snippet": "中央公園酒店是一家位於紐約市的4.0星級酒店，提供豪華的住宿體驗。酒店於2013年進行了最後一次翻新，確保客人能夠享受現代化的設施和舒適的環境。酒店擁有761間客房，提供 ..."}, {"title": "紐約中央公園艾美酒店(Le Méridien New York, Central Park)", "url": "https://www.agoda.com/zh-hk/viceroy-central-park-new-york_2/hotel/new-york-ny-us.html", "snippet": "紐約中央公園艾美酒店位於美國紐約市，是一家四星級酒店。這家酒店提供240間客房 ... 作為一家五星級酒店，紐約中央公園艾美酒店提供優質的服務和舒適的住宿環境 ..."}]
Thought: Now that I have found some hotels in New York, I will next find transportation options from Orlando to New York for the travel dates specified. I will use the QueryTransports API for this purpose.
Action: QueryTransports
Action Input: {"departure_city": "Orlando", "destination_city": "New York", "date": "2022-03-10", "requirement": "budget-friendly"}
Observation2: [{"title": "从奥兰多出发前往纽约的特价机票，往返 ...", "url": "https://www.tianxun.com/routes/orlb/nyca/orlando-to-new-york.html", "snippet": "查找从奥兰多飞往纽约最便宜的月份 ; 3月. ¥750 起 ; 4月. ¥927 起 ; 5月. ¥1,012 起 ; 6月. ¥1,107 起 ; 7月. ¥1,283 起."}, {"title": "从奥兰多国际出发前往纽约拉瓜迪亚的特价机票，往返 ...", "url": "https://www.tianxun.com/routes/mco/lga/orlando-international-to-new-york-laguardia.html", "snippet": "我们始终关注票价，方便您在几秒钟内锁定好价机票。目前，从奥兰多国际飞往纽约拉瓜迪亚最便宜的月份是十一月。"}]
Thought: Now that I have found some transportation options, I will proceed to find attractions in New York. I will use the QueryAttractions API to search for tourist attractions in New York.
Action: QueryAttractions
Action Input: {"destination": "New York"}
Observation3: - snippet: 從參觀紐約市最知名觀光景點開始：時代廣場、帝國大廈、自由女神像，然後利用剩餘的時間探索周圍地區推薦去處。 探索熱門體驗. 根據評等和預訂次數，看看其他旅客喜歡從事 ...
  title: 紐約市10 大最佳旅遊景點(2024) - Tripadvisor
  url: https://www.tripadvisor.com.hk/Attractions-g60763-Activities-New_York_City_New_York.html
- snippet: 紐約景點推薦 · 紐約景點#1 紐約中央公園 · 紐約景點#2 范德堡一號大樓 SUMMIT · 紐約景點#3 第五大道（Fifth Avenue）
    · 紐約景點#4 大都會藝術博物館The ...
  title: 【2024紐約景點】漫遊曼哈頓！26個必去行程&免費景點整理
  url: https://www.klook.com/zh-TW/blog/new-york-must-go/
- snippet: 【紐約NewYork景點推薦】紐約「10大必去」打卡景點整理懶人包 · 紐約NewYork景點推薦-10大必去景點 · 1.中央公園（Central
    Park） · 2.第五大道（Fifth Avenue） · 3.大都會 ...
  title: 【紐約NewYork景點推薦】紐約「10大必去」打卡景點整理懶人包
  url: https://schoolaplus.com/articles-detail.asp?seq=35
Thought: Now that I have found some attractions in New York, I will summarize the information and create a travel itinerary for the 5-day trip. I will use the Finish tool to provide the final answer.
Action: Finish
Action Input: {"plan details": "Day 1: Depart from Orlando to New York on March 10, 2022. Stay at the Park Central Hotel in Central Park. Visit the Empire State Building and Times Square. Have dinner at Lombardi's Pizza.
Day 2: Visit Central Park, the Metropolitan Museum of Art, and the American Museum of Natural History. Have lunch at Shake Shack and dinner at Le Pain Quotidien.
Day 3: Explore the Brooklyn Bridge, Brooklyn Heights, and DUMBO. Have lunch at Di Fara Pizza and dinner at Peter Luger Steak House.
Day 4: Visit the Statue of Liberty and Ellis Island. Have lunch at The Boil and dinner at Xi'an Famous Foods.
Day 5: Spend the day shopping on Fifth Avenue and visiting the Rockefeller Center. Have lunch at Shake Shack and dinner at Katz's Delicatessen."}
'''


def test_react_reflect_agent():
    llm = get_llm_backend(BACKEND_OPENAI_COMPATIBLE, API_BASE, API_KEY, LLM_NAME).run
    tool_list = [QueryAccommodations, QueryTransports, QueryGoogleDistanceMatrix, QueryAttractions, Finish]
    agent = ReactReflectAgent(reflect_llm=llm, react_llm=llm, example=EXAMPLE,
                              tool_list=tool_list, max_context_len=MAX_CONTEXT_LEN)
    response = agent.run("Can you help with a 5 day trip from Orlando to Paris? Departure date is April 10, 2022.",
                     text="given information")
    current_path = os.path.dirname(os.path.realpath(__file__))
    agent.save_agent_status(f"{current_path}/trajs/react_reflect_execution_log.jsonl")
    
    logger.info(f"5 day trip from Orlando to Paris:{response.answer}")


def get_args():
    parse = argparse.ArgumentParser()
    parse.add_argument("--model_name", type=str, default="Qwen1.5-32B-Chat", help="OpenAI客户端模型名")
    parse.add_argument("--base_url", type=str, default="http://10.44.115.108:1055/v1", help="OpenAI客户端模型地址")
    parse.add_argument("--api_key", type=str, default="EMPTY", help="OpenAI客户端api key")
    return parse.parse_args().__dict__


if __name__ == "__main__":
    args = get_args()
    API_BASE = args.pop("base_url")
    API_KEY = args.pop("api_key")
    LLM_NAME = args.pop("model_name")
    logger.info("react reflect agent test begin")
    test_react_reflect_agent()
    logger.info("react reflect agent test end")
