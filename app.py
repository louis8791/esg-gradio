"""公開資訊 CSV 資料瀏覽器 (Gradio + FastAPI) - PWA / RWD 版,可部署到 Render"""
import os
import io
import tempfile
from pathlib import Path

import pandas as pd
import requests
import urllib3
import gradio as gr
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "esg gradio" / "files" / "static"

DEFAULT_URL = os.environ.get(
    "CSV_URL",
    "https://data.tainan.gov.tw/File/ResourceCsvDownload/6c16b2c8-92b6-49d9-98b5-02966462172c",
)  # 換連結(也可在 Render 設定環境變數 CSV_URL)
CSV_PATH = "data01.csv"
ALL_COLS = "全部欄位"


# ====================== 資料處理 ======================
def fetch(url: str) -> pd.DataFrame:
    """下載 CSV、存檔、讀取並移除缺值列"""
    response = requests.get(url, verify=False, timeout=30)
    response.raise_for_status()
    raw = pd.read_csv(io.BytesIO(response.content), encoding="utf-8-sig")
    df = raw.dropna().reset_index(drop=True)
    df.attrs["removed_rows"] = len(raw) - len(df)
    return df


def summary_md(df: pd.DataFrame) -> str:
    mem = df.memory_usage(deep=True).sum() / 1024
    metrics = [
        ("📄 資料筆數", f"{len(df):,}"),
        ("🧱 欄位數", str(df.shape[1])),
        ("🔢 數值欄位", str(len(df.select_dtypes("number").columns))),
        ("🧹 移除空值列", f"{df.attrs.get('removed_rows', 0):,}"),
        ("💾 記憶體", f"{mem:,.1f} KB"),
    ]
    return '<div class="metric-grid">' + "".join(
        f'<div class="metric-card"><div>{label}</div><strong>{value}</strong></div>'
        for label, value in metrics
    ) + '</div>'


def search(df, keyword, column, max_rows):
    if df is None or df.empty:
        return pd.DataFrame(), "尚未載入資料"
    out = df
    keyword = (keyword or "").strip()
    if keyword:
        if column == ALL_COLS or column not in df.columns:
            mask = df.astype(str).apply(
                lambda s: s.str.contains(keyword, case=False, regex=False)
            ).any(axis=1)
        else:
            mask = df[column].astype(str).str.contains(keyword, case=False, regex=False)
        out = df[mask]
    info = f"🔍 符合 **{len(out):,}** / {len(df):,} 筆(顯示前 {min(int(max_rows), len(out))} 筆)"
    return out.head(int(max_rows)), info


def make_chart(df, column, top_n):
    if df is None or df.empty or column not in df.columns:
        return pd.DataFrame({"類別": [], "數量": []})
    counts = df[column].astype(str).value_counts().head(int(top_n)).reset_index()
    counts.columns = ["類別", "數量"]
    return counts


def export_csv(df, keyword, column):
    if df is None or df.empty:
        return None
    filtered, _ = search(df, keyword, column, len(df))
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv", prefix="filtered_result_")
    tmp.close()
    filtered.to_csv(tmp.name, index=False, encoding="utf-8-sig")
    return tmp.name


def export_excel(df, keyword, column):
    if df is None or df.empty:
        return None
    filtered, _ = search(df, keyword, column, len(df))
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx", prefix="filtered_result_")
    tmp.close()
    with pd.ExcelWriter(tmp.name, engine="openpyxl") as writer:
        filtered.to_excel(writer, index=False, sheet_name="資料")
        for row in writer.sheets["資料"].iter_rows():
            for cell in row:
                if cell.data_type == "f":
                    cell.data_type = "s"
    return tmp.name


def load(url):
    try:
        df = fetch(url.strip())
    except Exception as e:
        empty = pd.DataFrame()
        return (f"❌ 載入失敗:{e}", None, empty,
                gr.update(choices=[ALL_COLS], value=ALL_COLS), gr.update(choices=[], value=None), "", empty, empty)

    cols = list(df.columns)
    if len(df.select_dtypes("number").columns):
        num_desc = df.describe().round(2).reset_index()
    else:
        num_desc = pd.DataFrame({"提示": ["沒有數值欄位"]})
    info = pd.DataFrame({
        "欄位": cols,
        "型態": [str(t) for t in df.dtypes],
        "不重複值": [df[c].nunique() for c in cols],
        "範例": [str(df[c].iloc[0]) if len(df) else "" for c in cols],
    })
    return (
        f"✅ 載入成功，共 {len(df):,} 筆資料、{df.shape[1]} 個欄位（移除 {df.attrs.get('removed_rows', 0):,} 筆空值列）",
        df,
        df.head(50),
        gr.update(choices=[ALL_COLS] + cols, value=ALL_COLS),
        gr.update(choices=cols, value=cols[0]),
        summary_md(df),
        num_desc,
        info,
    )


# ====================== PWA:<head> 內容 ======================
PWA_HEAD = """
<link rel="manifest" href="/manifest.webmanifest">
<meta name="theme-color" content="#0d9488">
<meta name="application-name" content="公開資訊 CSV">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="公開資訊 CSV">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<link rel="apple-touch-icon" href="/pwa-static/icons/apple-touch-icon.png">
<link rel="icon" type="image/png" href="/pwa-static/icons/favicon.png">
<style>
  #pwa-install-btn {
    position: fixed; right: 16px; bottom: calc(16px + env(safe-area-inset-bottom, 0px));
    z-index: 9999; min-height: 48px; padding: 0 20px; border: 0; border-radius: 999px;
    background: #0d9488; color: #fff; font-size: 1rem; font-weight: 600;
    box-shadow: 0 6px 20px rgba(0,0,0,.25); cursor: pointer;
  }
</style>
<script>
(function () {
  // 註冊 Service Worker(必須由網站根目錄提供,才能控制整站)
  if ("serviceWorker" in navigator) {
    function registerWorker() {
      navigator.serviceWorker.register("/sw.js", { scope: "/" })
        .catch(function (e) { console.warn("Service Worker 註冊失敗:", e); });
    }
    if (document.readyState === "complete") registerWorker();
    else window.addEventListener("load", registerWorker);
  }

  // 自訂「安裝 App」按鈕(Chrome / Edge / Android)
  var deferredPrompt = null;
  function showInstallButton() {
    if (document.getElementById("pwa-install-btn")) return;
    var btn = document.createElement("button");
    btn.id = "pwa-install-btn";
    btn.type = "button";
    btn.textContent = "📲 安裝 App";
    btn.onclick = function () {
      btn.remove();
      if (!deferredPrompt) return;
      deferredPrompt.prompt();
      deferredPrompt.userChoice.finally(function () { deferredPrompt = null; });
    };
    document.body.appendChild(btn);
  }
  window.addEventListener("beforeinstallprompt", function (e) {
    e.preventDefault();
    deferredPrompt = e;
    if (document.body) showInstallButton();
    else document.addEventListener("DOMContentLoaded", showInstallButton);
  });
  window.addEventListener("appinstalled", function () {
    var b = document.getElementById("pwa-install-btn");
    if (b) b.remove();
  });
})();
</script>
"""

# ====================== RWD:CSS ======================
CSS = """
.gradio-container {
  max-width: 1200px !important; margin: auto;
  padding-left: max(12px, env(safe-area-inset-left)) !important;
  padding-right: max(12px, env(safe-area-inset-right)) !important;
}
#title { text-align: center; padding: 18px 0 4px; }
#title h1 { font-size: 2.1rem; margin-bottom: 4px; }
#title p { opacity: .7; margin: 0; }
#summary { overflow-x: auto; }
#summary table { margin: 0 auto; }

/* 平板以下 */
@media (max-width: 900px) {
  #title h1 { font-size: 1.7rem; }
}

/* 手機:所有橫排改為直排,按鈕加大好點擊 */
@media (max-width: 640px) {
  #title { padding-top: 10px; }
  #title h1 { font-size: 1.4rem; }
  #title p { font-size: .9rem; }
  .stack-mobile { flex-wrap: wrap !important; }
  .stack-mobile > * { min-width: 100% !important; flex: 1 1 100% !important; }
  #summary table { font-size: .8rem; }
  #summary th, #summary td { padding: 6px 4px !important; }
  button { min-height: 44px; }
  .gradio-container { padding-left: 8px !important; padding-right: 8px !important; }
}

/* App-style responsive UI */
#title { text-align: left; padding: 32px 30px; border-radius: 22px;
  background: linear-gradient(120deg, #0f766e, #235bdc);
  box-shadow: 0 12px 32px rgba(35,91,220,.16); margin-bottom: 14px; }
#title h1, #title p { color: white !important; }
#title p { opacity: .94; line-height: 1.65; }
.metric-grid { display: grid; grid-template-columns: repeat(auto-fit,minmax(150px,1fr)); gap: 14px; padding: 8px 0 18px; }
.metric-card { padding: 18px; border: 1px solid var(--border-color-primary, #dce4e9); border-radius: 16px; background: var(--block-background-fill, #fff); box-shadow: 0 3px 12px rgba(0,0,0,.04); }
.metric-card div { color: var(--body-text-color-subdued, #64748b); font-size: .9rem; }
.metric-card strong { display: block; margin-top: 8px; font-size: 1.8rem; color: #0d9488; }
@media (max-width: 900px) {
  .stack-mobile { flex-wrap: wrap !important; }
  .stack-mobile > * { min-width: 100% !important; flex: 1 1 100% !important; }
}
@media (max-width: 640px) {
  #title { padding: 22px 16px; }
  .metric-grid { grid-template-columns: repeat(2,minmax(0,1fr)); gap: 8px; }
  .metric-card { padding: 12px; }
  .metric-card strong { font-size: 1.4rem; }
}
@media (prefers-color-scheme: dark) {
  .metric-card strong { color: #5eead4; }
}
/* 安裝成 App 後隱藏 Gradio 頁尾,畫面更像原生 App */
@media (display-mode: standalone) {
  footer { display: none !important; }
}
"""

theme = gr.themes.Soft(primary_hue="teal", secondary_hue="cyan", neutral_hue="slate")

# ====================== Gradio 介面 ======================
with gr.Blocks(theme=theme, css=CSS, head=PWA_HEAD, title="公開資訊 CSV 資料瀏覽器") as demo:
    df_state = gr.State(None)

    gr.HTML("<div id='title'><h1>📊 公開資訊 CSV 資料瀏覽器</h1>"
            "<p>下載、搜尋、統計、視覺化與匯出，一站完成。支援手機、平板及電腦 App 安裝。</p></div>")

    with gr.Row(elem_classes="stack-mobile"):
        url_box = gr.Textbox(value=DEFAULT_URL, label="🔗 CSV 資料連結", lines=2, scale=5)
        load_btn = gr.Button("🔄 載入 / 重新下載", variant="primary", scale=1)
    status = gr.Markdown()
    summary = gr.HTML(elem_id="summary")

    with gr.Tabs():
        with gr.Tab("🗂️ 資料瀏覽"):
            with gr.Row(elem_classes="stack-mobile"):
                keyword = gr.Textbox(label="關鍵字", placeholder="輸入想搜尋的文字…", scale=3)
                col_dd = gr.Dropdown([ALL_COLS], value=ALL_COLS, label="搜尋欄位", scale=2)
                max_rows = gr.Slider(10, 500, value=50, step=10, label="顯示筆數", scale=2)
            search_info = gr.Markdown()
            table = gr.Dataframe(label="資料表", interactive=False, wrap=True, show_copy_button=True, show_fullscreen_button=True)
            with gr.Row(elem_classes="stack-mobile"):
                export_btn = gr.Button("⬇️ 匯出目前篩選結果 (CSV)")
                export_file = gr.File(label="下載檔案")
                excel_btn = gr.Button("⬇️ 匯出目前篩選結果 (Excel)")
                excel_file = gr.File(label="下載 Excel")

        with gr.Tab("📈 統計圖表"):
            with gr.Row(elem_classes="stack-mobile"):
                chart_col = gr.Dropdown([], label="選擇分類欄位", scale=3)
                top_n = gr.Slider(3, 30, value=10, step=1, label="顯示前 N 名", scale=2)
            plot = gr.BarPlot(x="類別", y="數量", title="各類別數量", height=380)

        with gr.Tab("🧾 欄位資訊"):
            gr.Markdown("#### 欄位結構")
            info_table = gr.Dataframe(interactive=False)
            gr.Markdown("#### 數值欄位統計")
            desc_table = gr.Dataframe(interactive=False)

    with gr.Accordion("📲 如何安裝成手機 / 電腦 App", open=False):
        gr.Markdown(
            "- **Android(Chrome)**:點右下角「📲 安裝 App」,或選單 → 加到主畫面\n"
            "- **iPhone / iPad(Safari)**:點下方「分享」→「加入主畫面」\n"
            "- **電腦(Chrome / Edge)**:網址列右側的安裝圖示 → 安裝"
        )

    # ---------------------- 事件綁定 ----------------------
    search_inputs = [df_state, keyword, col_dd, max_rows]
    search_outputs = [table, search_info]
    chart_inputs = [df_state, chart_col, top_n]
    load_outputs = [status, df_state, table, col_dd, chart_col, summary, desc_table, info_table]

    load_btn.click(load, url_box, load_outputs) \
        .then(search, search_inputs, search_outputs) \
        .then(make_chart, chart_inputs, plot)

    demo.load(load, url_box, load_outputs) \
        .then(search, search_inputs, search_outputs) \
        .then(make_chart, chart_inputs, plot)

    for comp in (keyword, col_dd, max_rows):
        comp.change(search, search_inputs, search_outputs)
    chart_col.change(make_chart, chart_inputs, plot)
    top_n.change(make_chart, chart_inputs, plot)
    export_btn.click(export_csv, [df_state, keyword, col_dd], export_file)
    excel_btn.click(export_excel, [df_state, keyword, col_dd], excel_file)


# ====================== FastAPI:PWA 路由 + 掛載 Gradio ======================
# 注意:PWA 檔案路由必須在 mount_gradio_app(path="/") 之前宣告
app = FastAPI(title="公開資訊 CSV 資料瀏覽器")


@app.get("/healthz", include_in_schema=False)
def healthz():
    return {"status": "ok"}


@app.get("/manifest.webmanifest", include_in_schema=False)
def manifest():
    return FileResponse(STATIC_DIR / "manifest.webmanifest", media_type="application/manifest+json")


@app.get("/sw.js", include_in_schema=False)
def service_worker():
    # Service Worker 必須從根路徑提供,且不能被長期快取
    return FileResponse(
        STATIC_DIR / "sw.js",
        media_type="application/javascript",
        headers={"Service-Worker-Allowed": "/", "Cache-Control": "no-cache"},
    )


@app.get("/offline.html", include_in_schema=False)
def offline():
    return FileResponse(STATIC_DIR / "offline.html", media_type="text/html")


app.mount("/pwa-static", StaticFiles(directory=STATIC_DIR), name="pwa-static")
app = gr.mount_gradio_app(app, demo, path="/")


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
