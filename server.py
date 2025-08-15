from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import os
import asyncio
from pydantic import BaseModel

app = FastAPI(title="Naver Blog Automation API")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발용, 나중에 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AutomationRequest(BaseModel):
    user_id: str = "default"
    action: str = "start_naver"

@app.get("/")
async def root():
    return {
        "message": "Naver Blog Automation API",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "message": "Render 서버 정상 운영 중"
    }

@app.post("/api/run-naver")
async def run_naver_automation(request: AutomationRequest):
    try:
        print(f"Starting automation for user: {request.user_id}")
        
        # Render 환경에서 헤드리스 Chrome으로 실행
        env = os.environ.copy()
        env['DISPLAY'] = ':99'  # 가상 디스플레이
        
        # Python 스크립트 실행
        result = subprocess.run([
            "python", "naver_manual_login.py"
        ], 
        capture_output=True, 
        text=True, 
        timeout=300,  # 5분 타임아웃
        env=env
        )
        
        if result.returncode == 0:
            return {
                "success": True,
                "message": "네이버 자동화가 시작되었습니다.",
                "output": result.stdout,
                "user_id": request.user_id
            }
        else:
            return {
                "success": False,
                "message": "Python 스크립트 실행 중 오류 발생",
                "error": result.stderr,
                "user_id": request.user_id
            }
            
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "message": "실행 시간 초과 (5분)",
            "user_id": request.user_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"서버 오류: {str(e)}"
        )

@app.get("/api/status")
async def get_status():
    return {
        "server": "Render",
        "service": "Naver Blog Automation",
        "free_tier": True,
        "limitations": [
            "15분 비활성 시 슬립 모드",
            "첫 요청 시 30초 콜드스타트",
            "월 750시간 제한"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)