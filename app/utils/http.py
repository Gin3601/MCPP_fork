import time
import requests
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("http")


class APIRequestError(RuntimeError):
    """API 请求失败异常"""
    
    def __init__(self, message: str, status_code: int | None = None, response_text: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text


session = requests.Session()
session.trust_env = False


def _clean_str(v: str | None) -> str:
    return (v or "").strip().strip('"').strip("'")


def _clean_url(url: str | None) -> str:
    u = _clean_str(url)
    return u


def _clean_key(key: str | None) -> str:
    k = _clean_str(key)
    if k.lower().startswith("bearer "):
        k = k.split(" ", 1)[1].strip()
    return k


def _headers(api_key: str | None) -> dict:
    k = _clean_key(api_key or settings.API_KEY)
    return {
        "Authorization": f"Bearer {k}",
        "Content-Type": "application/json",
    }


def post_edit(
    payload: dict,
    api_url: str | None = None,
    api_key: str | None = None,
    timeout: int = 180,
) -> dict:
    """调用 API 进行图像编辑"""
    url = _clean_url(api_url or settings.API_URL)
    if not url:
        logger.error("API_URL is empty. Check your .env / settings loading.")
        raise APIRequestError("API_URL is empty. Check your .env / settings loading.")
    if not (url.startswith("http://") or url.startswith("https://")):
        logger.error(f"Invalid API_URL: {url!r}")
        raise APIRequestError(f"Invalid API_URL: {url!r}")

    headers = _headers(api_key)
    logger.info(f"发起 POST 请求到 API: {url}")
    logger.debug(f"请求头: {headers}")
    logger.debug(f"请求体大小: {len(str(payload))} bytes")

    try:
        resp = session.post(url, headers=headers, json=payload, timeout=timeout)
        logger.info(f"API 响应状态码: {resp.status_code}")
    except requests.RequestException as e:
        logger.error(f"网络请求失败: {e}")
        raise APIRequestError(f"Network error: {e}") from e

    if resp.status_code >= 500:
        error_text = (resp.text or "")[:1500]
        logger.error(f"上游 API 返回服务器错误 ({resp.status_code}): {error_text}")
        raise APIRequestError(
            message=f"Upstream API returned {resp.status_code}: {error_text}",
            status_code=resp.status_code,
            response_text=error_text,
        )

    if resp.status_code >= 400:
        error_text = (resp.text or "")[:1500]
        logger.error(f"上游 API 返回客户端错误 ({resp.status_code}): {error_text}")
        raise APIRequestError(
            message=f"Upstream API returned {resp.status_code}: {error_text}",
            status_code=resp.status_code,
            response_text=error_text,
        )

    try:
        result = resp.json()
        logger.info("API 请求成功，返回有效 JSON 响应")
        logger.debug(f"响应内容: {result}")
        return result
    except ValueError:
        error_text = (resp.text or "")[:500]
        logger.error(f"API 返回无效 JSON 响应: {error_text}")
        raise APIRequestError(
            message="Invalid JSON response",
            status_code=resp.status_code,
            response_text=error_text,
        )


def get_json(
    url: str,
    api_key: str | None = None,
    timeout: int = 60,
) -> dict:
    """GET 一个 JSON（用于轮询 result_url）"""
    u = _clean_url(url)
    if not u:
        logger.error("result_url is empty")
        raise APIRequestError("result_url is empty")
    if not (u.startswith("http://") or u.startswith("https://")):
        logger.error(f"Invalid result_url: {u!r}")
        raise APIRequestError(f"Invalid result_url: {u!r}")

    headers = _headers(api_key)
    logger.info(f"发起 GET 请求到: {u}")
    logger.debug(f"请求头: {headers}")

    try:
        resp = session.get(u, headers=headers, timeout=timeout)
        logger.info(f"GET 请求响应状态码: {resp.status_code}")
    except requests.RequestException as e:
        logger.error(f"GET 请求网络错误: {e}")
        raise APIRequestError(f"Network error: {e}") from e

    if resp.status_code >= 400:
        error_text = (resp.text or "")[:1500]
        logger.error(f"上游 GET 请求返回错误 ({resp.status_code}): {error_text}")
        raise APIRequestError(
            message=f"Upstream GET returned {resp.status_code}: {error_text}",
            status_code=resp.status_code,
            response_text=error_text,
        )

    try:
        result = resp.json()
        logger.info("GET 请求成功，返回有效 JSON 响应")
        logger.debug(f"GET 响应内容: {result}")
        return result
    except ValueError:
        error_text = (resp.text or "")[:500]
        logger.error(f"GET 请求返回无效 JSON: {error_text}")
        raise APIRequestError(
            message="Invalid JSON response (GET)",
            status_code=resp.status_code,
            response_text=error_text,
        )


def wait_for_outputs(
    result_url: str,
    api_key: str | None = None,
    timeout_seconds: int = 180,
    poll_interval: float = 1.0,
) -> dict:
    """轮询 API 直到获取输出结果"""
    start = time.time()
    last: dict | None = None
    logger.info(f"开始轮询 API 结果，URL: {result_url}")
    logger.info(f"轮询超时时间: {timeout_seconds}秒，轮询间隔: {poll_interval}秒")

    while True:
        elapsed = time.time() - start
        logger.debug(f"轮询第 {elapsed/poll_interval:.0f} 次，已耗时: {elapsed:.1f}秒")
        
        last = get_json(result_url, api_key=api_key, timeout=60)

        data = last.get("data") if isinstance(last, dict) else None
        if not isinstance(data, dict):
            data = last if isinstance(last, dict) else {}

        status = (data.get("status") or "").lower()
        outputs = data.get("outputs") or []
        logger.info(f"轮询状态: {status}, 输出数量: {len(outputs)}")

        if outputs:
            logger.info("轮询成功获取输出结果")
            return last

        if status in {"completed", "succeeded"}:
            logger.error(f"任务已完成但输出为空: {data}")
            raise APIRequestError(f"Task completed but outputs empty: {data}")

        if status in {"failed", "canceled", "cancelled", "error"}:
            error_msg = data.get('error') or data
            logger.error(f"上游任务执行失败 ({status}): {error_msg}")
            raise APIRequestError(f"Upstream task {status}: {error_msg}")

        if time.time() - start > timeout_seconds:
            logger.error(f"轮询超时，最后状态: {status}, 数据: {data}")
            raise APIRequestError(f"Timeout waiting for outputs. Last status={status}, data={data}")

        logger.debug(f"继续轮询，等待 {poll_interval} 秒")
        time.sleep(poll_interval)