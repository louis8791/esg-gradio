"""既有 Render 啟動入口；ESG 實作位於 esg_csv/app.py。"""
import os

from esg_csv.app import app

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 7860)))
