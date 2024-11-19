# oai_img2text
利用openai接口进行图转文
如何使用？
1.源码运行
获取源码
git clone
安装依赖
pip install -r requirements.txt
新建.env文件，填入所需变量
运行python3 main.py
访问ip:54188即可
2.docker-compose部署（推荐）
version: '3.8'

services:
  img2text:
    image: gua12345/oai_img2text:latest  # 使用的 Docker 镜像
    environment:
      - API_BASE_URL=接口地址（不带路径）示例https://api.openai.com
      - OPENAI_API_KEY=你的apikey（都不用双引号）示例sk-111111111
    ports:
      - "54188:54188"  # 映射容器的 54188 端口到主机的 54188 端口
    restart: always  # 容器异常停止时自动重启
    network_mode: bridge  
环境变量如下
| 环境变量名         | 描述                           | 默认值                         |
|--------------------|--------------------------------|--------------------------------|
| `API_BASE_URL`     | API 请求地址                   | `https://api.openai.com`      |
| `OPENAI_API_KEY`   | OpenAI API 密钥                 | `sk-111111111`                |
| `MODEL`            | 使用的模型名称                 | `gpt-4o`                      |
| `CONCURRENCY`      | 并发限制 (最大并发数)          | `5`                           |
| `MAX_RETRIES`      | 最大重试次数                   | `5`                           |
| `FAVICON_URL`      | 网站的图标 URL                 | `/static/favicon.ico`         |
| `TITLE`            | 网站标题                       | `呱呱的oai图转文`              |
