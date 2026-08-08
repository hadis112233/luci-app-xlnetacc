import asyncio
import os
import re
from typing import Any

import ddddocr
from fastapi import FastAPI, Header, HTTPException, Request

MAX_IMAGE_BYTES = 1024 * 1024
MIN_CONFIDENCE = float(os.getenv("MIN_CONFIDENCE", "0.75"))
OCR_TOKEN = os.getenv("OCR_TOKEN", "")

app = FastAPI(title="XLNetAcc ddddocr service", version="1.0.0")
# 模型只在服务启动时加载一次，避免每次识别都产生数秒延迟。
ocr = ddddocr.DdddOcr(show_ad=False)
ocr.set_ranges(5)  # 大写英文字母 A-Z + 数字 0-9


def recognize(image: bytes) -> dict[str, Any]:
    result = ocr.classification(image, probability=True)
    charsets = result.get("charsets", [])
    probabilities = result.get("probability", [])
    code = ""
    confidences: list[float] = []

    for distribution in probabilities:
        if not distribution:
            continue
        index = max(range(len(distribution)), key=distribution.__getitem__)
        if index >= len(charsets):
            continue
        code += charsets[index]
        confidences.append(float(distribution[index]))

    code = re.sub(r"[^A-Z0-9]", "", code.upper())
    confidence = sum(confidences) / len(confidences) if confidences else 0.0
    accepted = len(code) == 4 and confidence >= MIN_CONFIDENCE
    return {
        "code": code if len(code) == 4 else "",
        "confidence": round(confidence, 4),
        "accepted": accepted,
    }


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/ocr")
async def recognize_image(request: Request, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    if OCR_TOKEN and authorization != f"Bearer {OCR_TOKEN}":
        raise HTTPException(status_code=401, detail="invalid OCR token")
    if not request.headers.get("content-type", "").startswith("image/"):
        raise HTTPException(status_code=415, detail="send the image as the raw request body")
    image = await request.body()
    if not image or len(image) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="image must be between 1 byte and 1 MiB")
    return await asyncio.to_thread(recognize, image)
