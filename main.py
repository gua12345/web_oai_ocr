import base64
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import fitz  # PyMuPDF
import logging
from fastapi.responses import JSONResponse
from io import BytesIO
from PIL import Image
import aiohttp
import asyncio
from fastapi import FastAPI, Request, UploadFile
import os
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles


# 配置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 加载 .env 文件（如果存在）
load_dotenv()

# 从环境变量中读取配置
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com")  # 默认 API 请求地址
API_KEY = os.getenv("OPENAI_API_KEY", "sk-111111111")  # 默认 API 密钥
MODEL = os.getenv("MODEL", "gpt-4o")  # 默认模型名称

# 并发限制和重试机制
CONCURRENCY = int(os.getenv("CONCURRENCY", 5))  # 默认并发限制为 5
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 5))  # 默认重试限制为 5

# 初始化 FastAPI 应用
app = FastAPI()

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="static"), name="static")

# 获取环境变量中的 FAVICON_URL
FAVICON_URL = os.getenv("FAVICON_URL", "/static/favicon.ico")
TITLE = os.getenv("TITLE", "呱呱的oai图转文")

# 配置 Jinja2 模板目录
templates = Jinja2Templates(directory="templates")

# 跨域支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源访问
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def process_image(session, image_data, semaphore, max_retries=MAX_RETRIES):
    """使用 OCR 识别图像并进行 Markdown 格式化"""
    system_prompt = """
    OCR识别图片上的内容，给出markdown的katex的格式的内容。
    选择题的序号使用A. B.依次类推。
    支持的主要语法：
    1. 基本语法：
       - 使用 $ 或 $$ 包裹行内或块级数学公式
       - 支持大量数学符号、希腊字母、运算符等
       - 分数：\\frac{分子}{分母}
       - 根号：\\sqrt{被开方数}
       - 上下标：x^2, x_n
    2. 极限使用：\\lim\\limits_x
    3. 参考以下例子格式：
    ### 35. 上3个无穷小量按照从低阶到高阶的排序是( )
    A.$\\alpha_1,\\alpha_2,\\alpha_3$ 
    B.$\\alpha_2,\\alpha_1,\\alpha_3$ 
    C.$\\alpha_1,\\alpha_3,\\alpha_2$ 
    D. $\\alpha_2,\\alpha_3,\\alpha_1$
    36. (I) 求 $\\lim\\limits_{x \\to +\\infty} \\frac{\\arctan 2x - \\arctan x}{\\frac{\\pi}{2} - \\arctan x}$;
        (II) 若 $\\lim\\limits_{x \\to +\\infty} x[1-f(x)]$ 不存在, 而 $l = \\lim\\limits_{x \\to +\\infty} \\frac{\\arctan 2x + [b-1-bf(x)]\\arctan x}{\\frac{\\pi}{2} - \\arctan x}$ 存在,
    试确定 $b$ 的值, 并求 (I)
    """
    for attempt in range(max_retries):
        try:
            async with semaphore:
                encoded_image = base64.b64encode(image_data).decode('utf-8')
                response = await session.post(
                    f"{API_BASE_URL}/v1/chat/completions",
                    headers={"Authorization": f"Bearer {API_KEY}"},
                    json={
                        "messages": [
                            {
                                "role": "system",
                                "content": system_prompt
                            },
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": "Analyze the image and provide the content in the specified format, you only need to return the content, before returning the content you need to say: 'This is the content:', add 'this is the end of the content' at the end of the returned content, do not have any additional text other than these two sentences and the returned content, don't reply to me before I upload the image!"
                                    },
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/png;base64,{encoded_image}"
                                        }
                                    }
                                ]
                            }
                        ],
                        "stream": False,
                        "model": MODEL,
                        "temperature": 0.5,
                        "presence_penalty": 0,
                        "frequency_penalty": 0,
                        "top_p": 1,
                    },
                )
                if response.status == 200:
                    result = await response.json()
                    return result['choices'][0]['message']['content']
                else:
                    raise Exception(f"请求失败, 状态码: {response.status}")
        except Exception as e:
            if attempt == max_retries - 1:
                return f"识别失败: {str(e)}"
            await asyncio.sleep(2 * attempt)  # 指数退避

#pdf接口为/process/pdf

@app.post("/process_one/image")
async def process_image_endpoint(file: UploadFile):
    try:
        image_data = await file.read()
        if not image_data:
            logger.error("未收到有效图片数据")
            return JSONResponse({"status": "error", "message": "未收到有效图片数据"})

        logger.info(f"开始处理图片: {file.filename}")
        semaphore = asyncio.Semaphore(CONCURRENCY)

        async with aiohttp.ClientSession() as session:
            result = await process_image(session, image_data, semaphore)

        if result and result.startswith("This is the content:"):
            # 提取 "This is the content:" 到 "this is the end of the content" 之间的内容
            start_index = result.find("This is the content:") + len("This is the content:")
            end_index = result.find("this is the end of the content.") - len("this is the end of the content.")
            content = result[start_index:end_index].strip()
            # 移除 ```markdown 和 ```
            content = content.replace("```markdown", "").replace("```", "").strip()
            return JSONResponse({"status": "success", "content": content})
        else:
            logger.error("返回了无效数据，未以'This is the content'开头")
            logger.error(result)
            return JSONResponse({"status": "error", "message": "返回无效数据"})
    except Exception as e:
        logger.error(f"图片处理失败: {e}")
        return JSONResponse({"status": "error", "message": str(e)})

@app.post("/process/image")
async def process_image_endpoint(file: UploadFile):
    RETRY_DELAY = 0.5  # 每次重试之间的延迟时间（秒）

    # 缓存文件数据
    file_data = await file.read()
    if not file_data:
        logger.error("未收到有效图片数据")
        return JSONResponse({"status": "error", "message": "未收到有效图片数据"})

    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"开始处理图片 (尝试 {attempt + 1}/{MAX_RETRIES}): {file.filename}")
            semaphore = asyncio.Semaphore(CONCURRENCY)

            # 异步处理图片
            async with aiohttp.ClientSession() as session:
                result = await process_image(session, file_data, semaphore)

            # 验证返回数据有效性
            if result and result.startswith("This is the content:"):
                start_index = result.find("This is the content:") + len("This is the content:")
                end_index = result.find("this is the end of the content.") - len("this is the end of the content.")
                content = result[start_index:end_index].strip()
                content = content.replace("```markdown", "").replace("```", "").strip()
                return JSONResponse({"status": "success", "content": content})
            else:
                logger.error("返回了无效数据，未以'This is the content'开头")
                logger.error(result)
                raise ValueError("返回无效数据")
        except Exception as e:
            logger.error(f"图片处理失败 (尝试 {attempt + 1}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))
            else:
                return JSONResponse({"status": "error", "message": f"图片处理失败: {e}"})

def pdf_to_images(pdf_bytes: bytes, dpi: int = 300) -> list:
    """
    使用 PyMuPDF 将 PDF 转换为图片。
    :param pdf_bytes: PDF 文件的字节数据。
    :param dpi: 图像分辨率 (300 DPI)。
    :return: PIL 图像列表。
    """
    images = []
    try:
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        logger.info(f"PDF 文件包含 {len(pdf_document)} 页")

        for page_number in range(len(pdf_document)):
            page = pdf_document.load_page(page_number)
            pix = page.get_pixmap(dpi=dpi)
            image = Image.open(BytesIO(pix.tobytes("png")))
            images.append(image)
        return images
    except Exception as e:
        logger.error(f"PDF 转图片失败: {e}")
        raise


async def upload_image_to_endpoint(image_data: bytes, page_number: int, semaphore: asyncio.Semaphore):
    url = "http://127.0.0.1:8000/process_one/image"
    for attempt in range(MAX_RETRIES):
        try:
            async with semaphore, aiohttp.ClientSession() as session:
                logger.info(f"开始处理第 {page_number} 页，尝试 {attempt + 1}/{MAX_RETRIES}")

                files = aiohttp.FormData()
                files.add_field(
                    "file",
                    image_data,
                    filename=f"page_{page_number}.png",
                    content_type="image/png",
                )

                async with session.post(url, data=files) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("status") == "success":
                            logger.info(f"第 {page_number} 页处理成功")
                            return result["content"]
                        else:
                            raise Exception(result.get("message", "未知错误"))
        except Exception as e:
            logger.error(f"第 {page_number} 页处理失败: {e}")
            if attempt == MAX_RETRIES - 1:
                return f"第 {page_number} 页识别失败: {e}"
            await asyncio.sleep(2 * (attempt + 1))


@app.post("/process/pdf")
async def process_pdf_endpoint(file: UploadFile):
    """
    处理上传的 PDF 文件，将每页图片转换为文本。
    """
    try:
        pdf_data = await file.read()
        logger.info(f"开始处理 PDF 文件: {file.filename}")

        # 将 PDF 转换为图片
        images = pdf_to_images(pdf_data, dpi=300)
        logger.info(f"PDF 文件成功转换为 {len(images)} 页图片")

        # 控制并发
        semaphore = asyncio.Semaphore(CONCURRENCY)
        tasks = []

        # 创建任务列表
        for page_number, image in enumerate(images, start=1):
            with BytesIO() as buffer:
                image.save(buffer, format="PNG")
                image_data = buffer.getvalue()
                tasks.append(upload_image_to_endpoint(image_data, page_number, semaphore))

        # 等待所有任务完成
        results = await asyncio.gather(*tasks)

        # 合并所有页面的结果，不包含多余文字
        combined_text = "\n\n".join(results)

        return JSONResponse({"status": "success", "content": combined_text})

    except Exception as e:
        logger.error(f"处理 PDF 文件失败: {e}")
        return JSONResponse({"status": "error", "message": str(e)})

# 根路由，渲染 web.html
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("web.html", {"request": request, "favicon_url": FAVICON_URL, "title": TITLE })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=54188)
