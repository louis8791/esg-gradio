# 📊 台南市開放資料瀏覽器(PWA + RWD)

使用 [Gradio](https://www.gradio.app/) + FastAPI 製作的台南市政府開放資料(CSV)瀏覽器。
支援 **PWA**(可安裝成手機 / 電腦 App)與 **RWD**(手機、平板、桌機自動適應版面)。

## ✨ 功能

- 自動下載 CSV 並移除缺值列(`dropna`)
- 關鍵字搜尋(全部欄位或指定欄位)
- 匯出篩選結果為 CSV(UTF-8 with BOM,Excel 可直接開啟中文)
- 任選欄位繪製前 N 名長條圖
- 欄位結構與數值欄位統計摘要

## 📱 PWA 與 RWD 說明

| 項目 | 實作 |
|---|---|
| Web App Manifest | `static/manifest.webmanifest`(名稱、圖示、主題色、standalone 模式) |
| Service Worker | `static/sw.js`,由 `/sw.js` 根路徑提供;離線時顯示 `offline.html` |
| 圖示 | `static/icons/`(192、512、maskable、Apple Touch Icon、favicon) |
| 安裝按鈕 | 瀏覽器符合安裝條件時,右下角出現「📲 安裝 App」 |
| RWD | CSS media queries:手機(≤640px)橫排元件自動改直排、按鈕加大、表格可橫向捲動、支援瀏覽器安全區域(瀏海) |
| 深色模式 | 沿用 Gradio 主題,離線頁也支援 |

> **注意**:資料需要連網下載,離線時只會顯示友善的離線頁面,不會有舊資料。
> PWA 需要 **HTTPS** 才能安裝,Render 預設提供 HTTPS;本機 `localhost` 也可測試。

## 📁 專案結構

```
esg_csv/
├── app.py
├── requirements.txt
├── README.md
├── static/           # ESG 專用 PWA 資源
├── legacy/           # 原始課堂版本，非部署入口
└── tainan-gradio-pwa.zip
```

此資料夾包含現行 ESG 主程式；儲存庫根目錄的 `app.py`、`requirements.txt` 是既有 Render 服務的相容入口，根目錄 `render.yaml` 仍是 ESG 部署設定。

## 💻 本機執行

```bash
pip install -r requirements.txt
python app.py
```

開啟 http://localhost:7860

## 🚀 部署到 Render

1. 把整個儲存庫推上 GitHub，保留根目錄部署入口及 `esg_csv/static/`。
2. Render → **New → Web Service** → 選擇你的 repo（Root Directory 留空，使用根目錄；本指南適用於尚未建立服務時）。
3. 設定:

   | 欄位 | 值 |
   |---|---|
   | Runtime | Python 3 |
   | Build Command | `pip install -r requirements.txt` |
   | Start Command | `uvicorn app:app --host 0.0.0.0 --port $PORT` |
   | Health Check Path | `/healthz` |
   | Instance Type | Free |

4. Environment 新增 `PYTHON_VERSION` = `3.11.9`。
5. Create Web Service。部署完成後用 Render 網址開啟即可。

也可以選 **New → Blueprint**，使用儲存庫根目錄的 `render.yaml`。既有服務無須另建。

## 📲 安裝成 App

- **Android(Chrome)**:點右下角「📲 安裝 App」,或選單 → 加到主畫面
- **iPhone / iPad(Safari)**:分享 → 加入主畫面
- **電腦(Chrome / Edge)**:網址列右側的安裝圖示

## ⚙️ 環境變數

| 變數 | 說明 | 預設 |
|---|---|---|
| `CSV_URL` | 預設載入的 CSV 連結 | 台南市開放資料連結 |
| `PORT` | 服務埠號(Render 自動提供) | `7860` |

## 🔄 更新 PWA 快取

修改 `static/sw.js` 內的 `VERSION`(例如 `v1` → `v2`),使用者下次開啟時舊快取會自動清除。

## ⚠️ 注意事項

- Render 免費方案閒置約 15 分鐘會休眠,再次開啟需約 30~60 秒喚醒。
- 程式使用 `verify=False` 下載資料(原始程式即如此),會關閉 SSL 憑證驗證,僅建議用於公開資料。
- 資料來源:[台南市政府資料開放平台](https://data.tainan.gov.tw/)


## App 介面升級

支援任意可讀取的公開 CSV 網址（預設保留台南市資料）、響應式統計卡片、CSV / Excel 匯出、資料表複製與全螢幕操作。Chrome / Edge 可透過網站安裝功能安裝 PWA；iOS Safari 可加入主畫面。
