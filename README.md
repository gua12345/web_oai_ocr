# web_oai_img2text
利用 OpenAI 接口进行图转文,支持pdf，适配chat2api，自动排除降智以及chat2api图片上传失败返回
![image](https://github.com/user-attachments/assets/54e85ac9-7695-482b-acff-9bcd66b11ef0)


## 如何使用？

### 1. 源码运行
1. 获取源码：
   ```bash
   git clone https://github.com/gua12345/oai_img2text.git
   ```
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 在 `.env` 文件里填入所需变量。
4. 运行：
   ```bash
   python3 main.py
   ```
5. 访问 `ip:54188/pwd` 即可。

### 2. Docker-Compose 部署（推荐）
```yaml
version: '3.8'

services:
  img2text:
    image: gua12345/oai_img2text:latest  # 使用的 Docker 镜像
    environment:
      - API_BASE_URL=接口地址（不带路径）示例 https://api.openai.com
      - OPENAI_API_KEY=你的 API 密钥（都不用双引号）示例 sk-111111111
    ports:
      - "54188:54188"  # 映射容器的 54188 端口到主机的 54188 端口
    restart: always  # 容器异常停止时自动重启
    network_mode: bridge
```

## 环境变量如下

| 环境变量名         | 描述                           | 默认值                         |
|--------------------|--------------------------------|--------------------------------|
| `API_BASE_URL`     | API 请求地址                   | `https://api.openai.com`      |
| `OPENAI_API_KEY`   | OpenAI API 密钥                 | `sk-111111111`                |
| `MODEL`            | 使用的模型名称                 | `gpt-4o`                      |
| `CONCURRENCY`      | 并发限制 (最大并发数)          | `5`                           |
| `MAX_RETRIES`      | 最大重试次数                   | `5`                           |
| `FAVICON_URL`      | 网站的图标 URL                 | `/static/favicon.ico`         |
| `TITLE`            | 网站标题                       | `呱呱的oai图转文`              |
| `PASSWORD`         | 网站路径密码                   | `pwd`                          |
| `BACK_URL`         | 服务后端代码，设置成https的不过cloudflare的反代域名，能解决cloudflare 100秒请求超时的限制,不设置就获取你网页当前窗口的域名或ip| |

## 注意事项
### BACK_URL带https://
### 处理图片返回响应的时间比较长，如果你使用了cloudflare的cdn就会受到cloudflare 100秒请求超时的限制导致网页无法接收到正确的响应,目前解决办法两个1.不使用cloudflare cdn 2.多域名反代内网54188端口，用不使用cloudflare cdn的域名作为BACK_URL

