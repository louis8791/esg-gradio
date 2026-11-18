# 📊 台南市開放資料瀏覽器（課堂舊版）

> 此資料夾保存原始非 PWA 課堂版，僅供對照。現行 ESG 主程式和 PWA 資源位於上一層 `esg_csv/`，舊版部署設定不應套用到既有服務。

使用 [Gradio](https://www.gradio.app/) 製作的台南市政府開放資料(CSV)瀏覽器,
可下載、搜尋、統計與視覺化資料。

## ✨ 功能

- 自動下載 CSV 並移除缺值列(`dropna`)
- 關鍵字搜尋(全部欄位或指定欄位)
- 匯出篩選結果為 CSV(UTF-8 with BOM,Excel 可直接開啟中文)
- 任選欄位繪製前 N 名長條圖
- 欄位結構與數值欄位統計摘要

## 📁 專案結構

```
.
├── app.py             # Gradio 主程式
├── requirements.txt   # 套件清單
├── render.yaml        # Render 部署設定(選用)
├── .gitignore
└── README.md
```

## 💻 本機執行

```bash
pip install -r requirements.txt
python app.py
```

瀏覽器開啟 http://localhost:7860

## 🚀 部署到 Render

### 方法一:手動建立

1. 把專案推上 GitHub。
2. 登入 [Render](https://render.com/),點 **New → Web Service**,選擇你的 GitHub repo。
3. 填寫設定:

   | 欄位 | 值 |
   |---|---|
   | Runtime | Python 3 |
   | Build Command | `pip install -r requirements.txt` |
   | Start Command | `python app.py` |
   | Instance Type | Free |

4. (建議)在 **Environment** 新增 `PYTHON_VERSION` = `3.11.9`。
5. 點 **Create Web Service**,等待部署完成後即可用 Render 提供的網址開啟。

### 方法二:Blueprint(使用 render.yaml)

在 Render 選 **New → Blueprint**,指向這個 repo,Render 會自動讀取 `render.yaml`。

## ⚙️ 環境變數

| 變數 | 說明 | 預設 |
|---|---|---|
| `CSV_URL` | 預設載入的 CSV 連結 | 台南市開放資料連結 |
| `PORT` | 服務埠號(Render 自動提供) | `7860` |

## ⚠️ 注意事項

- Render 免費方案閒置約 15 分鐘後會休眠,再次開啟時需要約 30~60 秒喚醒。
- 程式使用 `verify=False` 下載資料(原始程式即如此),會關閉 SSL 憑證驗證,僅建議用於公開資料。
- 資料來源:[台南市政府資料開放平台](https://data.tainan.gov.tw/)
