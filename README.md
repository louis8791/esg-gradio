# ESG 公開資料分析

使用 Gradio 瀏覽、搜尋及統計公開 CSV 資料，並匯出資料。應用程式與 PWA 資源位於 [esg_csv](esg_csv/)，原始課堂版本及壓縮檔也保存在該目錄。

## 啟動

Render 沿用儲存庫根目錄的啟動與部署設定。本機可用相同入口啟動。

```sh
pip install -r requirements.txt
uvicorn app:app --host 127.0.0.1 --port 7860
```

課堂 RAG 文件問答已搬至獨立的 [louis8791/rag-qa-pwa](https://github.com/louis8791/rag-qa-pwa)。
