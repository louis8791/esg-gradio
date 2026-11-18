"""台南市開放資料瀏覽器 (Gradio) - 可部署到 Render"""
import os
import tempfile

import pandas as pd
import requests
import urllib3
import gradio as gr

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DEFAULT_URL = os.environ.get(
    "CSV_URL",
    "https://data.tainan.gov.tw/File/ResourceCsvDownload/6c16b2c8-92b6-49d9-98b5-02966462172c",
)  # 換連結(也可在 Render 設定環境變數 CSV_URL)
CSV_PATH = "data01.csv"
ALL_COLS = "全部欄位"


# ---------------------- 資料處理 ----------------------
def fetch(url: str) -> pd.DataFrame:
    """下載 CSV、存檔、讀取並移除缺值列"""
    response = requests.get(url, verify=False, timeout=30)
    response.raise_for_status()
    with open(CSV_PATH, "wb") as file:
        file.write(response.content)
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")  # 繁體中文
    return df.dropna().reset_index(drop=True)


def summary_md(df: pd.DataFrame) -> str:
    mem = df.memory_usage(deep=True).sum() / 1024
    return (
        f"| 📄 資料筆數 | 🧱 欄位數 | 🔢 數值欄位 | 💾 記憶體 |\n"
        f"|:---:|:---:|:---:|:---:|\n"
        f"| **{len(df):,}** | **{df.shape[1]}** | "
        f"**{len(df.select_dtypes('number').columns)}** | **{mem:,.1f} KB** |"
    )


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
    tmp = tempfile.NamedTemporaryFile(
        delete=False, suffix=".csv", prefix="filtered_result_"
    )
    tmp.close()
    filtered.to_csv(tmp.name, index=False, encoding="utf-8-sig")
    return tmp.name


# ---------------------- 載入流程 ----------------------
def load(url):
    try:
        df = fetch(url.strip())
    except Exception as e:
        empty = pd.DataFrame()
        return (f"❌ 載入失敗:{e}", None, empty,
                gr.update(), gr.update(), "", empty, empty)

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
        f"✅ 載入成功,共 {len(df):,} 筆資料(已移除缺值列)",
        df,
        df.head(50),
        gr.update(choices=[ALL_COLS] + cols, value=ALL_COLS),
        gr.update(choices=cols, value=cols[0]),
        summary_md(df),
        num_desc,
        info,
    )


# ---------------------- 介面 ----------------------
theme = gr.themes.Soft(primary_hue="teal", secondary_hue="cyan", neutral_hue="slate")

css = """
.gradio-container {max-width: 1200px !important; margin: auto;}
#title {text-align: center; padding: 18px 0 4px;}
#title h1 {font-size: 2.1rem; margin-bottom: 4px;}
#title p {opacity: .7; margin: 0;}
"""

with gr.Blocks(theme=theme, css=css, title="台南開放資料瀏覽器") as demo:
    df_state = gr.State(None)

    gr.HTML("<div id='title'><h1>📊 台南市開放資料瀏覽器</h1>"
            "<p>下載、搜尋、統計與視覺化,一站完成</p></div>")

    with gr.Row():
        url_box = gr.Textbox(value=DEFAULT_URL, label="🔗 CSV 資料連結", scale=5)
        load_btn = gr.Button("🔄 載入 / 重新下載", variant="primary", scale=1)
    status = gr.Markdown()
    summary = gr.Markdown()

    with gr.Tabs():
        # ---- 分頁 1:資料瀏覽 ----
        with gr.Tab("🗂️ 資料瀏覽"):
            with gr.Row():
                keyword = gr.Textbox(label="關鍵字", placeholder="輸入想搜尋的文字…", scale=3)
                col_dd = gr.Dropdown([ALL_COLS], value=ALL_COLS, label="搜尋欄位", scale=2)
                max_rows = gr.Slider(10, 500, value=50, step=10, label="顯示筆數", scale=2)
            search_info = gr.Markdown()
            table = gr.Dataframe(label="資料表", interactive=False, wrap=True)
            with gr.Row():
                export_btn = gr.Button("⬇️ 匯出目前篩選結果 (CSV)")
                export_file = gr.File(label="下載檔案")

        # ---- 分頁 2:統計圖表 ----
        with gr.Tab("📈 統計圖表"):
            with gr.Row():
                chart_col = gr.Dropdown([], label="選擇分類欄位", scale=3)
                top_n = gr.Slider(3, 30, value=10, step=1, label="顯示前 N 名", scale=2)
            plot = gr.BarPlot(x="類別", y="數量", title="各類別數量", height=420)

        # ---- 分頁 3:欄位資訊 ----
        with gr.Tab("🧾 欄位資訊"):
            gr.Markdown("#### 欄位結構")
            info_table = gr.Dataframe(interactive=False)
            gr.Markdown("#### 數值欄位統計")
            desc_table = gr.Dataframe(interactive=False)

    # ---------------------- 事件綁定 ----------------------
    search_inputs = [df_state, keyword, col_dd, max_rows]
    search_outputs = [table, search_info]
    chart_inputs = [df_state, chart_col, top_n]
    load_outputs = [status, df_state, table, col_dd, chart_col, summary, desc_table, info_table]

    load_btn.click(load, url_box, load_outputs) \
        .then(search, search_inputs, search_outputs) \
        .then(make_chart, chart_inputs, plot)

    # 頁面開啟時自動載入
    demo.load(load, url_box, load_outputs) \
        .then(search, search_inputs, search_outputs) \
        .then(make_chart, chart_inputs, plot)

    for comp in (keyword, col_dd, max_rows):
        comp.change(search, search_inputs, search_outputs)
    chart_col.change(make_chart, chart_inputs, plot)
    top_n.change(make_chart, chart_inputs, plot)
    export_btn.click(export_csv, [df_state, keyword, col_dd], export_file)


if __name__ == "__main__":
    # Render 會提供 PORT 環境變數,並要求綁定 0.0.0.0
    port = int(os.environ.get("PORT", 7860))
    demo.queue().launch(server_name="0.0.0.0", server_port=port)
