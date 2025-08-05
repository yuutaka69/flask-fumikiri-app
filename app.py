# app.py
from flask import Flask, render_template, request
import pandas as pd
import folium
import os

app = Flask(__name__)

# --- データ読み込み ---
DATA_PATH = 'data/踏切_緯度経度追加_v5.csv'
df = pd.read_csv(DATA_PATH)

# --- フィルター用の選択肢を事前に作成 ---
FILTER_COLS = {
    '線名': '線名',
    '支社名': '支社名',
    '箇所名（系統名なし）': '箇所名（系統名なし）',
    '踏切種別': '踏切種別'
}
filters = {}
for key, col in FILTER_COLS.items():
    if col in df.columns:
        filters[key] = sorted(df[col].dropna().astype(str).unique().tolist())

def format_kilopost(value):
    if pd.isna(value): return ""
    try:
        value = float(value)
        kilo = int(value / 1000)
        meter = value % 1000
        return f"{kilo}k{meter:05.1f}m"
    except (ValueError, TypeError):
        return str(value)

@app.route('/', methods=['GET', 'POST'])
def index():
    filtered_df = df.copy()

    if request.method == 'POST':
        # フォームから送信された値でフィルタリング
        search_name = request.form.get('search_name', '')
        if search_name and '踏切名' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['踏切名'].notna() & filtered_df['踏切名'].str.contains(search_name, na=False)]

        for key, col in FILTER_COLS.items():
            selected_value = request.form.get(key, 'すべて')
            if selected_value != 'すべて' and col in filtered_df.columns:
                filtered_df = filtered_df[filtered_df[col] == selected_value]

    map_html = None
    if not filtered_df.empty:
        center_lat = filtered_df['Lat'].mean()
        center_lon = filtered_df['Lon'].mean()
        m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

        for _, row in filtered_df.iterrows():
            if pd.notna(row['Lat']) and pd.notna(row['Lon']):
                gmap_link = f"https://www.google.com/maps?q={row['Lat']},{row['Lon']}"
                formatted_kilopost = format_kilopost(row.get('中心位置キロ程'))
                popup_html = f"""
                    <b>踏切名:</b> {row.get('踏切名', '名称不明')}<br>
                    <b>線名:</b> {row.get('線名', '')}<br>
                    <b>キロ程:</b> {formatted_kilopost}<br>
                    <a href="{gmap_link}" target="_blank" rel="noopener noreferrer">Google Mapで開く</a>
                """
                popup = folium.Popup(popup_html, max_width=300)
                folium.Marker(
                    location=[row['Lat'], row['Lon']],
                    popup=popup,
                    tooltip=row.get('踏切名', '')
                ).add_to(m)
        
        # 地図をHTMLとして取得（ヘッダーとフッターは不要）
        map_html = m._repr_html_()

    return render_template('index.html', map_html=map_html, filters=filters, count=len(filtered_df), request=request)

if __name__ == '__main__':
    app.run(debug=True)
