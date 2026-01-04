import os
from pathlib import Path
from enum import Enum

from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Form
from fastapi.staticfiles import StaticFiles

from app.utils.logger import get_logger

# 核心服务
from app.services.MCPP_fork_main import run as main_run, ServiceError

logger = get_logger("main")

app = FastAPI(title="Image Generator API")

# 挂载 /media：让保存到 MEDIA_ROOT 的图片可以被 URL 访问到
MEDIA_ROOT = os.getenv("MEDIA_ROOT", "./media")
Path(MEDIA_ROOT).mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=MEDIA_ROOT), name="media")


def collect_images(image1: UploadFile, image2: UploadFile, image3: UploadFile) -> dict:
    """
    收集上传的图片
    """
    return {
        "image1": image1,
        "image2": image2,
        "image3": image3,
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


# 定义功能枚举类，用于生成下拉选择框
class FeatureEnum(str, Enum):
    product_main = "商品主图"
    product_display_1 = "商品展示图1"
    product_size = "商品尺寸图"
    product_display_2 = "商品展示图2"
    scene_display_1 = "场景展示图1"
    scene_display_2 = "场景展示图2"


@app.post("/generate/upload")
async def generate_image(
    request: Request,
    image1: UploadFile = File(...),
    image2: UploadFile = File(...),
    image3: UploadFile = File(...),
    feature: FeatureEnum = Form(FeatureEnum.product_main),  # 使用枚举类型实现下拉选择
):
    images = collect_images(image1, image2, image3)
    try:
        return await main_run(images, request=request, feature=feature)
    except ServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception("generate_image crashed")
        raise HTTPException(status_code=500, detail="Internal server error")