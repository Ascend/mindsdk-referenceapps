import json
from typing import List

from langchain_community.tools import DuckDuckGoSearchResults
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from utils.log import LOGGER as logger

from toolmngt.api import API


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

    def check_api_call_correctness(self, response: dict, groundtruth=None) -> bool:
        """
        Checks if the response from the API call is correct.

        Parameters:
        - response (dict): the response from the API call.
        - groundtruth (dict): the groundtruth response.

        Returns:
        - is_correct (bool): whether the response is correct.
        """

        ex = response.get("exception")

        if ex is not None:
            return False
        else:
            return True

    def call(self, input_parameters: dict, **kwargs) -> dict:
        """
        Calls the API with the given parameters.

        Parameters:

            input_parameters = {
                'query': query
            }

        Returns:
        - response (str): the response from the API call.
        """
        logger.debug(f"{input_parameters}")
        query = input_parameters.get('query', "")

        try:
            responses = self.call_duck_duck_go_search(query=query, count=4)
            logger.debug(f"responses is {responses}")
            output = ""
            if len(responses) > 0:
                for r in responses:
                    output += self.format_step(r)
            else:
                output = "Bing search error"
        except Exception as e:
            exception = str(e)
            return {'api_name': self.__class__.__name__, 'input': input_parameters,
                    'output': f'Search error,please try again',
                    'exception': exception}
        else:
            return {'api_name': self.__class__.__name__, 'input': input_parameters, 'output': output,
                    'exception': None}

    def format_result(self, res):
        snippet_idx = res.find("snippet:")
        title_idx = res.find("title:")
        link_idx = res.find("link:")
        snippet = res[snippet_idx + len("snippet:"):title_idx]
        title = res[title_idx + len("title:"):link_idx]
        link = res[link_idx + len("link:"):]
        return {"snippet": snippet.replace("<b>", "").replace("</b>", ""), "title": title, "link": link}

    def call_duck_duck_go_search(self, query: str, count: int) -> List[str]:
        try:
            logger.debug(f"search DuckDuckGo({query}, {count})")
            duck_duck_search = DuckDuckGoSearchAPIWrapper(max_results=count)
            search = DuckDuckGoSearchResults(api_wrapper=duck_duck_search)
            self.bingsearch_results = []
            temp = search.run(query)
            logger.debug(temp)

            for x in temp.split("["):
                snippet = x.split("]")[0].strip()
                if len(snippet) == 0:
                    continue
                logger.debug(f"snippet is {snippet}")
                self.bingsearch_results.append(self.format_result(snippet))
            logger.success(f"{json.dumps(self.bingsearch_results, indent=4)}")
        except Exception as e:
            self.scratchpad += f'Search error {str(e)}, please try again'

        return [x['snippet'] for x in self.bingsearch_results]
