import json
from typing import List
import re
import time

from langchain_community.tools import DuckDuckGoSearchResults
from loguru import logger

from agent_sdk.toolmngt.api import API


class DuckDuckGoSearch(API):
    name = "DuckDuckGoSearch"
    description = ("DuckDuckGoSearch engine can search for rich external knowledge on the Internet based on keywords, "
                   "which can compensate for knowledge fallacy and knowledge outdated.")
    input_parameters = {
        'query': {'type': 'str', 'description': "the query string to be search"}
    }
    output_parameters = {
        'information': {'type': 'str', 'description': 'the result information from Bing search engine'}
    }
    usage = ("DuckDuckGoSearch[query], which searches the exact detailed query on the Internet and returns the "
             "relevant information to the query. Be specific and precise with your query to increase the chances of "
             "getting relevant results. For example, DuckDuckGoSearch[popular dog breeds in the United States]")

    def __init__(self) -> None:
        self.scratchpad = ""
        self.bingsearch_results = ""

    def format_tool_input_parameters(self, llm_output) -> dict:
        input_parameters = {"query": llm_output}
        return input_parameters

    def call(self, input_parameter: dict, **kwargs) -> dict:
        logger.debug(f"{input_parameter}")
        query = input_parameter.get('query', "")

        try:
            responses = call_duck_duck_go_search(query=query, count=4)
            logger.debug(f"responses is {responses}")
            output = ""
            if len(responses) > 0:
                for r in responses:
                    output += self.format_step(r)
            else:
                output = "duck duck search error"
                return self.make_response(input_parameter, results=responses, exception=output)
            return self.make_response(input_parameter, results=responses, exception="")
        except Exception as e:
            exception = str(e)
            return self.make_response(input_parameter, results="", exception=exception)


def call_duck_duck_go_search(query: str, count: int) -> List[str]:
    retry = 1
    while retry <= 3:
        try:
            logger.debug(f"search DuckDuckGo({query}, {count})")
            search = DuckDuckGoSearchResults(output_format="list", max_results=count)
            return search.invoke(query)
        except Exception as e:
            retry += 1
            time.sleep(1)
            if retry > 3:
                logger.error(e)
                return []
