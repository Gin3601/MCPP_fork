import base64
import io
import os
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
        # 处理所有可能的图像键，包括参考图像
        urls = []
        for key, value in images.items():
            if isinstance(value, str) and value.strip():
                urls.append(value.strip())
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
        prompt = "请根据提供的四张图像生成一个新的组合图像"  # 默认提示词
    
    # 读取图片并转换为base64编码
  
    
    image_base64_list = []
    
    # 根据不同功能加载对应的固定参考图像
    if feature == "商品尺寸图":
        reference_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "input", "reference_size.jpg")
    elif feature == "商品主图":
        reference_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "input", "reference_main1.jpg")
    else:
        reference_file_path = None
    
    if reference_file_path and os.path.exists(reference_file_path):
        try:
            with open(reference_file_path, 'rb') as f:
                content = f.read()
                base64_str = base64.b64encode(content).decode('utf-8')
                ext = reference_file_path.split('.')[-1].lower()
                base64_url = f"data:image/{ext};base64,{base64_str}"
                image_base64_list.append(base64_url)
            logger.info(f"加载了参考图像: {reference_file_path}")
        except Exception as e:
            logger.error(f"加载参考图像失败: {e}")
    
    # 处理上传的图像
    for key, upload_file in images.items():
        # 读取文件内容
        content = await upload_file.read()
        # 转换为base64编码
        base64_str = base64.b64encode(content).decode('utf-8')
        # 获取文件扩展名
        ext = upload_file.filename.split('.')[-1].lower() if upload_file.filename else 'png'
        # 构建base64字符串
        base64_url = f"data:image/{ext};base64,{base64_str}"
        image_base64_list.append(base64_url)
        # 关闭文件
        await upload_file.close()

    try:
        if not image_base64_list:
            raise ServiceError("缺少图片数据：必须上传至少一张图片")

        payload = {
            "prompt": prompt,
            "images": image_base64_list,
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