1 在Dockerfile同级目录创建package目录

2 将start.sh tei.patch存放到package目录中

3 在package目录存放好protoc软件包
从网站上下载：https://github.com/protocolbuffers/protobuf/releases/tag/v29.3
如下载29.3版本：protoc-29.3-linux-aarch_64.zip

4 package目录存放Ascend-cann-kernels  Ascend-cann-toolkit  Ascend-cann-nnal, Ascend-mindxsdk-mxrag相关软件包，确保正确配套的卡和系统架构

5 构建环境上提前准备好ubuntu:20.04基础镜像

6 在Dockerfile同级目录下执行构建命令
docker build -t 镜像tag --network host --build-arg ARCH=$(uname -m)  --build-arg PLATFORM=<chip-type> -f Dockerfile .

chip-type取值请根据在服务器上执行npu-smi info 命令进行查询，将查询到的"Name"字段最后一位数字删除后值修改PLATFORM字段

安装rust相关 依赖依赖网络，可能比较慢

7 在package目录下执行 nodejs server.js &
```
准备server.js文件，和上述软件包放置于相同目录
const http = require('http');
const fs = require('fs');
const path = require('path');

const port = 3000;
const directory = __dirname;

const server = http.createServer((req, res) => {
	const filePath = path.join(directory, req.url);

	if (req.url === '/files') {
		// return all file names in current directory
		fs.readdir(directory, (err, files) => {
			if (err) {
				res.writeHead(500, {
					'Content-Type': 'text/plain'
				});
				res.end('Internal Server Error\n');
				return;
			}
			res.writeHead(200, {
				'Content-Type': 'application/json'
			});
			res.end(JSON.stringify(files));
		});
	} else {
		fs.stat(filePath, (err, stats) => {
			if (err || !stats.isFile()) {
				res.writeHead(404, {
					'Content-Type': 'text/plain'
				});
				res.end('Not Found\n');
				return;
			}
			fs.createReadStream(filePath).pipe(res);
		});
	}
});

server.listen(port, () => {
	console.log(`Server is running at http://localhost:${port}`);
});
```