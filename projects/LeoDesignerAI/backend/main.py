from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uuid
import os
import shutil

app = FastAPI(title="Leo Designer AI Server", version="1.0.0")

# CORS - 允许APP访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 目录
BASE_DIR = os.path.dirname(__file__)
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 挂载静态文件
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# ====== 数据模型 ======
class GenerateRequest(BaseModel):
    prompt: str
    model: str = "flux"
    size: str = "1024x1024"

class GenerateResponse(BaseModel):
    url: str
    id: str

# ====== 健康检查 ======
@app.get("/")
async def root():
    return {"status": "ok", "app": "LeoDesignerAI", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy", "uptime": "running"}

# ====== AI生成图片 ======
@app.post("/generate", response_model=GenerateResponse)
async def generate_image(req: GenerateRequest):
    """
    AI生成图片
    V1: 返回占位图
    V2: 接Flux API / DALL-E 3
    """
    img_id = str(uuid.uuid4())[:8]
    
    # TODO V2: 接 Flux API
    # from ai.image import generate_with_flux
    # url = generate_with_flux(req.prompt, req.size)
    
    # V1: 占位图（用picsum）
    placeholder_url = f"https://picsum.photos/seed/{img_id}/1024/1024"
    
    return GenerateResponse(
        url=placeholder_url,
        id=img_id
    )

# ====== AI抠图 ======
@app.post("/cutout")
async def cutout_image(image: UploadFile = File(...)):
    """
    AI抠图 - 去除背景
    V1: 保存原图返回
    V2: 接rembg/SAM2
    """
    img_id = str(uuid.uuid4())[:8]
    
    # 保存上传的图片
    input_path = os.path.join(UPLOAD_DIR, f"{img_id}_input.png")
    output_path = os.path.join(UPLOAD_DIR, f"{img_id}_cutout.png")
    
    with open(input_path, "wb") as f:
        content = await image.read()
        f.write(content)
    
    # TODO V2: 接 rembg / SAM2
    # from ai.cutout import remove_background
    # remove_background(input_path, output_path)
    
    # V1: 直接复制原图作为占位
    shutil.copy(input_path, output_path)
    
    return JSONResponse({
        "url": f"/static/uploads/{img_id}_cutout.png",
        "id": img_id
    })

# ====== 换背景 ======
@app.post("/swap-background")
async def swap_background(
    image: UploadFile = File(...),
    background: UploadFile = File(None),
    prompt: str = "自然背景"
):
    """
    AI换背景
    V1: 返回原图
    V2: 接SD inpainting
    """
    img_id = str(uuid.uuid4())[:8]
    input_path = os.path.join(UPLOAD_DIR, f"{img_id}_input.png")
    
    with open(input_path, "wb") as f:
        content = await image.read()
        f.write(content)
    
    # TODO V2: 接 AI inpainting
    output_path = input_path  # V1: 返回原图
    
    return JSONResponse({
        "url": f"/static/uploads/{img_id}_input.png",
        "id": img_id
    })

# ====== 保存作品 ======
@app.post("/save")
async def save_artwork(
    image: UploadFile = File(...),
    prompt: str = "",
    category: str = "ai_generated"
):
    """保存作品到本地"""
    artwork_id = str(uuid.uuid4())[:8]
    ext = os.path.splitext(image.filename or ".png")[1] or ".png"
    filename = f"{artwork_id}{ext}"
    path = os.path.join(UPLOAD_DIR, filename)
    
    with open(path, "wb") as f:
        content = await image.read()
        f.write(content)
    
    return JSONResponse({
        "id": artwork_id,
        "url": f"/static/uploads/{filename}",
        "prompt": prompt,
        "category": category
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
