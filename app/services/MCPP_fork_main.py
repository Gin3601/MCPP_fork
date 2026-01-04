from app.utils.http import post_edit, wait_for_outputs
from app.utils.logger import get_logger
from app.config import settings
from app.prompts import get_prompt  # 导入新的提示词获取函数

logger = get_logger("MCPP_main")


class ServiceError(Exception):
    pass


def _normalize_images(images) -> list[str]:
    """标准化图像输入格式"""
    if isinstance(images, list):
        urls = [x for x in images if isinstance(x, str) and x.strip()]
        return urls

    if isinstance(images, dict):
        keys = ["image1", "image2", "image3"]
        urls = []
        for k in keys:
            v = images.get(k)
            if isinstance(v, str) and v.strip():
                urls.append(v.strip())
        if not urls and isinstance(images.get("images"), list):
            urls = [x for x in images["images"] if isinstance(x, str) and x.strip()]
        return urls

    return []


async def run(images, request=None, feature="combine_images"):
    logger.info("MCPP_main start")
    
    # 直接使用Python函数获取提示词
    prompt = get_prompt(feature)
    
    # 确保获取到了有效的提示词
    if not prompt:
        prompt = "请根据提供的三张图像生成一个新的组合图像"  # 默认提示词
    
    # 保存上传的图片并获取URL
    from app.services.image_store import save_uploadfile_as_url
    saved_images = {}
    for key, upload_file in images.items():
        saved_images[key] = await save_uploadfile_as_url(upload_file, request)

    try:
        image_urls = _normalize_images(saved_images)
        if not image_urls:
            raise ServiceError("缺少图片URL：images 必须是 URL 列表，或包含 image1/image2/image3 的 dict")

        payload = {
            "prompt": prompt,
            "images": image_urls,
            "enable_sync_mode": True,
            "enable_base64_output": False,
            "resolution": "1k",
        }

        result = post_edit(
            api_url=settings.API_URL,
            api_key=settings.API_KEY,
            payload=payload,
        )

        data = result.get("data") if isinstance(result, dict) else None
        if not isinstance(data, dict):
            logger.error("MCPP_main invalid response: %s", result)
            raise ServiceError("上游返回格式异常")

        status = (data.get("status") or "").lower()
        outputs = data.get("outputs") or []

        if outputs:
            logger.info("MCPP_main success (sync)")
            return {"status": "success", "output": outputs[0], "mode": "sync"}

        result_url = (data.get("urls") or {}).get("get")
        if not result_url:
            logger.error("MCPP_main no outputs and no result url: %s", result)
            raise ServiceError("模型未返回结果且缺少结果查询地址")

        final = wait_for_outputs(
            result_url=result_url,
            api_key=settings.API_KEY,
            timeout_seconds=180,
            poll_interval=1.0,
        )
        fdata = final.get("data") if isinstance(final, dict) else None
        foutputs = (fdata or {}).get("outputs") or []
        if not foutputs:
            logger.error("MCPP_main async done but still no outputs: %s", final)
            raise ServiceError("模型未返回结果")

        logger.info("MCPP_main success (async fallback)")
        return {"status": "success", "output": foutputs[0], "mode": "async"}

    except ServiceError:
        raise
    except Exception:
        logger.exception("MCPP_main crashed")
        raise ServiceError("MCPP_main internal error")