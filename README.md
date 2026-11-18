# ESG & RAG · Gradio 應用系統

本儲存庫包含兩套獨立的課堂應用，使用相同的 Gradio、FastAPI、PWA 與 Render 技術，但各自保有主程式、相依套件及 PWA 資源。

| 專案 | 功能 | 開啟 |
| --- | --- | --- |
| ESG CSV | 公開資訊 CSV 瀏覽、搜尋、統計、匯出 | [esg_csv](esg_csv/) |
| RAG 文件問答 | PDF／DOCX、八種檢索策略、Groq、Word／CSV 匯出 | [rag_qa](rag_qa/) |

## 專案結構

```text
.
├── esg_csv/          # ESG 應用程式（現行部署）
│   ├── app.py
│   ├── requirements.txt
│   ├── README.md
│   ├── static/
│   └── legacy/       # 原始課堂版本
├── rag_qa/           # RAG 問答應用程式
│   ├── app.py
│   ├── requirements.txt
│   ├── requirements-lite.txt
│   ├── render.yaml
│   ├── README.md
│   └── static/
├── app.py            # 現有 ESG Render 相容啟動入口
├── requirements.txt  # 引用 ESG 套件清單
├── render.yaml       # 現有 ESG 部署設定
└── README.md
```

兩個原始 ZIP 壓縮檔仍保存在相應專案資料夾中。

## 部署

- ESG：保留現有 Render 服務設定；根目錄啟動指令 `uvicorn app:app --host 0.0.0.0 --port $PORT` 不變。
- RAG：參考 [RAG 部署說明](rag_qa/README.md)，另建服務，Root Directory 使用 `rag_qa`。完整模式可能需要付費實例；輕量模式有檢索能力限制。

兩套 PWA 的圖示、名稱、快取與部署設定各自獨立。目前不抽離共用模組，以免讓兩個服務互相依賴。
