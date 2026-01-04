# 图像生成 API

## 快速开始

### 环境变量

创建 `.env` 文件，填入：

```env
# 必填：302 API 凭证
API_URL="https://api.302.ai/v1/xxx"
API_KEY="your-api-key"

# 可选：媒体文件保存目录（默认 ./media）
MEDIA_ROOT="./media"

# 可选：用于生成外部可访问的图片 URL（如果部署在公网）
PUBLIC_BASE_URL="https://your-domain.com"
```

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动服务

```bash
python -m uvicorn app.main:app --reload
```

访问 http://localhost:8000/docs 查看 API 文档。

## API 接口

### POST /generate/upload

上传 3 张图片并使用自定义提示词生成新图像。

**参数：**
- `image1`: 第一张图像
- `image2`: 第二张图像
- `image3`: 第三张图像
- `prompt`: 自定义提示词

**响应：**

```json
{
  "status": "success",
  "output": "https://your-domain.com/media/generated-image.jpg",
  "mode": "sync"
}
```