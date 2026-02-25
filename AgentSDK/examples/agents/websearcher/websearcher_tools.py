"""
Copyright 2026 Huawei Technologies Co., Ltd

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

websearcher_tools = {
    "search": {
        "name": "search",
        "description": "Performs batched web searches: supply an array 'query'; the tool retrieves the top 10 results for each query in on call",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "list[str]",
                    "items": {"type": "string"},
                    "description": "Array os query strings. Include multiple complementary search queries in a single call."
                }
            },
            "required": [
                "query"
            ]
        }
    }
}