import os
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from app.utils.logger import get_logger

logger = get_logger("image_store")

MEDIA_ROOT = os.getenv("MEDIA_ROOT", "./media")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").strip()


class ServiceError(Exception):
    pass


def _ensure_media_root() -> Path:
    root = Path(MEDIA_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    logger.info(f"媒体根目录已确保存在: {root}")
    return root


def _guess_suffix(filename: str) -> str:
    suf = Path(filename or "").suffix.lower()
    result = suf if suf else ".bin"
    logger.debug(f"文件 {filename} 的后缀被推测为: {result}")
    return result


def _build_base_url(request: Any = None, base_url: Optional[str] = None) -> str:
    if base_url and base_url.strip():
        url = base_url.strip().rstrip("/")
        logger.info(f"使用传入的 base_url: {url}")
        return url
    if PUBLIC_BASE_URL:
        url = PUBLIC_BASE_URL.rstrip("/")
        logger.info(f"使用环境变量 PUBLIC_BASE_URL: {url}")
        return url
    if request is not None:
        url = str(request.base_url).rstrip("/")
        logger.info(f"使用请求的 base_url: {url}")
        return url
    logger.error("缺少 base_url：请传 request 或设置环境变量 PUBLIC_BASE_URL")
    raise ServiceError("缺少 base_url：请传 request 或设置环境变量 PUBLIC_BASE_URL")


async def save_uploadfile_as_url(
    upload_file: Any,
    request: Any = None,
    base_url: Optional[str] = None,
) -> str:
    """保存上传的文件并返回可访问的 URL"""
    filename = getattr(upload_file, "filename", "未知文件名")
    logger.info(f"开始保存上传文件: {filename}")
    
    root = _ensure_media_root()
    suffix = _guess_suffix(filename)
    name = f"{uuid.uuid4().hex}{suffix}"
    dst = root / name
    logger.info(f"文件将保存到: {dst}")

    try:
        with dst.open("wb") as f:
            total_size = 0
            while True:
                chunk = await upload_file.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)
                total_size += len(chunk)
        logger.info(f"文件 {filename} 保存成功，大小: {total_size} bytes")
    except Exception as e:
        logger.error(f"保存文件 {filename} 失败: {e}")
        raise ServiceError(f"保存文件失败: {e}")

    try:
        await upload_file.close()
        logger.debug(f"上传文件 {filename} 已关闭")
    except Exception as e:
        logger.warning(f"关闭上传文件 {filename} 时出错: {e}")

    base = _build_base_url(request=request, base_url=base_url)
    file_url = f"{base}/media/{name}"
    logger.info(f"文件 URL 已生成: {file_url}")
    return file_url