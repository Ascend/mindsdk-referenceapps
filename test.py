curl -X POST -H "Content-Type:application/json" -H "Accept:application/json" -d '{
"model": "Qwen1.5-32B-Chat",
"messages": [
    {
        "role": "user",
        "content": "curl命令报错：暂时无法载入，服务载入中或服务运行错误，是什么原因？"
    }
]
}' https://mindie02.test.osinfra.cn/v1/chat/completions




curl -X POST -H "Content-Type:application/json" -H "Accept:application/json" -d '{
"model": "Qwen1.5-32B-Chat",
"messages": [
    {
        "role": "user",
        "content": "你是什么模型？"

    }
]
}' http://127.0.0.1:1025/v1/chat/completions




import requests
requests.post("https://mindie02.test.osinfra.cn/v1/chat/completions", data={"model": "Qwen1.5-32B-Chat",
"messages": [
    {
        "role": "user",
        "content": "帮我指定一个北京的旅游计划"
    }
]})




$headers = @{
    "Content-Type" = "application/json"
    "Accept" = "application/json"
}
$body = @{
    "model" = "Qwen1.5-32B-Chat"
    "messages" = @(
        @{
            "role" = "user"
            "content" = "hello"
        }
    )
} | ConvertTo-Json
Invoke-WebRequest -Uri "https://mindie02.test.osinfra.cn/v1/chat/completions" -Method POST -Headers $headers -Body $body