import os
from pathlib import Path

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


def collect_images(image1: UploadFile, image2: UploadFile, image3: UploadFile, image4: UploadFile) -> dict:
    """
    收集上传的图片
    
    Args:
        image1: 纸巾图像
        image2: 6寸餐盘图像
        image3: 9寸餐盘图像
        image4: 刀叉图像
        
    Returns:
        包含所有上传图片的字典
    """
    return {
        "image1": image1,  # 纸巾图像
        "image2": image2,  # 6寸餐盘图像
        "image3": image3,  # 9寸餐盘图像
        "image4": image4,  # 刀叉图像
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


# 商品主图生成端点
@app.post("/generate/product_main")
async def generate_product_main(
    request: Request,
    image1: UploadFile = File(..., description="纸巾图像"),
    image2: UploadFile = File(..., description="6寸餐盘图像"),
    image3: UploadFile = File(..., description="9寸餐盘图像"),
    image4: UploadFile = File(..., description="刀叉图像"),
):
    logger.info("接收到商品主图生成请求")
    images = collect_images(image1, image2, image3, image4)
    try:
        result = await main_run(images, request=request, feature="商品主图")
        logger.info("商品主图生成请求处理成功")
        return result
    except ServiceError as e:
        logger.error(f"商品主图生成失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception("generate_product_main crashed")
        raise HTTPException(status_code=500, detail="Internal server error")

# 商品展示图1生成端点
@app.post("/generate/product_display_1")
async def generate_product_display_1(
    request: Request,
    image1: UploadFile = File(..., description="纸巾图像"),
    image2: UploadFile = File(..., description="6寸餐盘图像"),
    image3: UploadFile = File(..., description="9寸餐盘图像"),
    image4: UploadFile = File(..., description="刀叉图像"),
):
    logger.info("接收到商品展示图1生成请求")
    images = collect_images(image1, image2, image3, image4)
    try:
        result = await main_run(images, request=request, feature="商品展示图1")
        logger.info("商品展示图1生成请求处理成功")
        return result
    except ServiceError as e:
        logger.error(f"商品展示图1生成失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception("generate_product_display_1 crashed")
        raise HTTPException(status_code=500, detail="Internal server error")

# 商品尺寸图生成端点
@app.post("/generate/product_size")
async def generate_product_size(
    request: Request,
    image1: UploadFile = File(..., description="纸巾图像"),
    image2: UploadFile = File(..., description="6寸餐盘图像"),
    image3: UploadFile = File(..., description="9寸餐盘图像"),
    image4: UploadFile = File(..., description="刀叉图像"),
):
    logger.info("接收到商品尺寸图生成请求")
    # 收集基本图像
    images = collect_images(image1, image2, image3, image4)
    try:
        result = await main_run(images, request=request, feature="商品尺寸图")
        logger.info("商品尺寸图生成请求处理成功")
        return result
    except ServiceError as e:
        logger.error(f"商品尺寸图生成失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception("generate_product_size crashed")
        raise HTTPException(status_code=500, detail="Internal server error")

# 商品展示图2生成端点
@app.post("/generate/product_display_2")
async def generate_product_display_2(
    request: Request,
    image1: UploadFile = File(..., description="纸巾图像"),
    image2: UploadFile = File(..., description="6寸餐盘图像"),
    image3: UploadFile = File(..., description="9寸餐盘图像"),
    image4: UploadFile = File(..., description="刀叉图像"),
):
    logger.info("接收到商品展示图2生成请求")
    images = collect_images(image1, image2, image3, image4)
    try:
        result = await main_run(images, request=request, feature="商品展示图2")
        logger.info("商品展示图2生成请求处理成功")
        return result
    except ServiceError as e:
        logger.error(f"商品展示图2生成失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception("generate_product_display_2 crashed")
        raise HTTPException(status_code=500, detail="Internal server error")

# 场景展示图1生成端点
@app.post("/generate/scene_display_1")
async def generate_scene_display_1(
    request: Request,
    image1: UploadFile = File(..., description="纸巾图像"),
    image2: UploadFile = File(..., description="6寸餐盘图像"),
    image3: UploadFile = File(..., description="9寸餐盘图像"),
    image4: UploadFile = File(..., description="刀叉图像"),
):
    logger.info("接收到场景展示图1生成请求")
    images = collect_images(image1, image2, image3, image4)
    try:
        result = await main_run(images, request=request, feature="场景展示图1")
        logger.info("场景展示图1生成请求处理成功")
        return result
    except ServiceError as e:
        logger.error(f"场景展示图1生成失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception("generate_scene_display_1 crashed")
        raise HTTPException(status_code=500, detail="Internal server error")

# 场景展示图2生成端点
@app.post("/generate/scene_display_2")
async def generate_scene_display_2(
    request: Request,
    image1: UploadFile = File(..., description="纸巾图像"),
    image2: UploadFile = File(..., description="6寸餐盘图像"),
    image3: UploadFile = File(..., description="9寸餐盘图像"),
    image4: UploadFile = File(..., description="刀叉图像"),
):
    logger.info("接收到场景展示图2生成请求")
    images = collect_images(image1, image2, image3, image4)
    try:
        result = await main_run(images, request=request, feature="场景展示图2")
        logger.info("场景展示图2生成请求处理成功")
        return result
    except ServiceError as e:
        logger.error(f"场景展示图2生成失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception("generate_scene_display_2 crashed")
        raise HTTPException(status_code=500, detail="Internal server error")