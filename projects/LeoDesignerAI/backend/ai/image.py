"""
AI图像处理模块
V1: 占位实现
V2: 接入真实AI模型
"""

# TODO V2: 接入 Flux API
# import requests
# FLUX_API_KEY = os.getenv("FLUX_API_KEY", "")
# FLUX_API_URL = "https://api.bfl.ml/v1/generation"

def generate_with_flux(prompt: str, size: str = "1024x1024") -> str:
    """
    使用Flux API生成图片
    返回图片URL
    """
    # TODO V2: 实现
    # headers = {"Authorization": f"Bearer {FLUX_API_KEY}", "Content-Type": "application/json"}
    # payload = {"prompt": prompt, "size": size}
    # resp = requests.post(FLUX_API_URL, json=payload, headers=headers)
    # return resp.json()["url"]
    
    # V1: 占位
    return f"https://picsum.photos/seed/{hash(prompt)}/1024/1024"
