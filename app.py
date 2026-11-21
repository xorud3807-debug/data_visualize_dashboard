import streamlit as st
import pandas as pd
import os

# 페이지 기본 설정
st.set_page_config(
    page_title="2024년 소방청 화재통계 대시보드",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS (KPI 카드 스타일링)
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1f2937, #111827);
        border: 1px solid #374151;
        border-radius: 12px;
        padding: 20px;
        color: white;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    .metric-title {
        font-size: 0.95rem;
        font-weight: 500;
        color: #9ca3af;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    .metric-sub {
        font-size: 0.85rem;
        color: #d1d5db;
        margin-top: 6px;
    }
    .card-fire { border-top: 4px solid #ef4444; }
    .card-casualty { border-top: 4px solid #f97316; }
    .card-damage { border-top: 4px solid #eab308; }
</style>
""", unsafe_allow_html=True)

# 데이터 로드 (캐싱 적용)
@st.cache_data
def load_data():
    file_path = "소방청_연간화재통계_20241231.csv"
    if not os.path.exists(file_path):
        # 현재 스크립트 위치 기준으로도 탐색
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, file_path)
    
    # cp949 인코딩으로 로드
    df = pd.read_csv(file_path, encoding="cp949")
    if "일시" in df.columns:
        df["일시"] = pd.to_datetime(df["일시"], errors="coerce")
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# 대시보드 헤더
st.title("2024년 소방청 전국 화재통계 분석 대시보드")
st.caption("데이터 출처: 소방청 국가화재정보시스템 (2024년 1월 1일 ~ 12월 31일)")

# 사이드바 (기본 안내 및 향후 필터 확장 대비)
# with st.sidebar:
#     st.header("⚙️ 대시보드 설정")
#     st.info("좌측 사이드바에서 추후 지역별/기간별 필터를 추가할 수 있습니다.")
#     st.write(f"**총 데이터 건수:** {len(df):,}건")

# 최상단 KPI 메트릭 계산
total_fire_count = len(df)
total_casualties = df["인명피해(명)소계"].sum()
total_deaths = df["사망"].sum()
total_injuries = df["부상"].sum()

# 재산피해(천원 단위)
total_property_loss_thousand = df["재산피해소계"].sum()
total_property_loss_won = total_property_loss_thousand * 1000

# 억 원 / 조 원 포맷팅
loss_in_hundred_millions = total_property_loss_won / 100_000_000

# 최상단 메트릭 카드 레이아웃
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div class="metric-card card-fire">
        <div class="metric-title">총 화재 건수</div>
        <div class="metric-value">{total_fire_count:,} <span style="font-size:1.2rem; font-weight:normal;">건</span></div>
        <div class="metric-sub">2024년 연간 누적 화재 발생 건수</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card card-casualty">
        <div class="metric-title">총 인명 피해</div>
        <div class="metric-value">{total_casualties:,} <span style="font-size:1.2rem; font-weight:normal;">명</span></div>
        <div class="metric-sub">사망 <b>{total_deaths:,}</b>명 &nbsp;|&nbsp; 부상 <b>{total_injuries:,}</b>명</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card card-damage">
        <div class="metric-title">총 재산 피해</div>
        <div class="metric-value">{loss_in_hundred_millions:,.1f} <span style="font-size:1.2rem; font-weight:normal;">억 원</span></div>
        <div class="metric-sub">{total_property_loss_thousand:,} 천원 ({total_property_loss_won:,.0f}원)</div>
    </div>
    """, unsafe_allow_html=True)

import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 시도별 · 시군구 막대그래프
# ==========================================
st.markdown("---")
st.subheader("시도별 · 시군구 화재 발생 건수 분석")

# 시도 목록 (화재 발생 건수가 많은 순서로 기본 제공)
sido_list = df["시도"].value_counts().index.tolist()

col_sido_sel, col_sido_sort = st.columns([2, 1])
with col_sido_sel:
    selected_sido_bar = st.selectbox("분석할 시도를 선택하세요 :", options=sido_list, index=0, key="bar_sido_select")
with col_sido_sort:
    sort_order = st.radio("시군구 정렬 기준", options=["화재건수 많은 순", "시군구 이름순"], horizontal=True, key="bar_sort_order")

# 선택된 시도 데이터 집계
sido_df = df[df["시도"] == selected_sido_bar]
sigungu_counts = sido_df["시_군_구"].value_counts().reset_index()
sigungu_counts.columns = ["시_군_구", "화재건수"]

if sort_order == "화재건수 많은 순":
    sigungu_counts = sigungu_counts.sort_values(by="화재건수", ascending=False)
else:
    sigungu_counts = sigungu_counts.sort_values(by="시_군_구", ascending=True)

# 시도 내 비중 계산
sigungu_counts["비중(%)"] = (sigungu_counts["화재건수"] / len(sido_df) * 100).round(1)

# 막대그래프 생성
fig_bar = px.bar(
    sigungu_counts,
    x="시_군_구",
    y="화재건수",
    text="화재건수",
    color="화재건수",
    color_continuous_scale="Reds",
    hover_data={"시_군_구": True, "화재건수": ":,", "비중(%)": ":.1f%"},
    labels={"시_군_구": "시·군·구", "화재건수": "화재 발생 건수 (건)"}
)

fig_bar.update_traces(
    texttemplate="%{text:,}건",
    textposition="outside",
    cliponaxis=False
)

fig_bar.update_layout(
    title=dict(
        text=f"<b>[{selected_sido_bar}] 시·군·구별 화재 발생 건수 (총 {len(sido_df):,}건 / {len(sigungu_counts)}개 구역)</b>",
        font=dict(size=16)
    ),
    xaxis_tickangle=-35,
    xaxis=dict(title="<b>시·군·구</b>"),
    yaxis=dict(title="<b>화재 발생 건수 (건)</b>"),
    coloraxis_showscale=False,
    height=480,
    margin=dict(l=40, r=40, t=60, b=80),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)"
)

st.plotly_chart(fig_bar, width="stretch")

top_sigungu = sigungu_counts.iloc[0] if not sigungu_counts.empty else None
if top_sigungu is not None:
    st.caption(f" **{selected_sido_bar} 1위 발생 지역:** **{top_sigungu['시_군_구']}** ({top_sigungu['화재건수']:,}건, {selected_sido_bar} 전체의 {top_sigungu['비중(%)']}%)")

st.markdown("---")

# ==========================================
# 월별 화재 발생 추이 (꺾은선 그래프)
# ==========================================
st.subheader("📈 월별 화재 발생 추이 (2024년)")

# 월 데이터 추출
df["월"] = df["일시"].dt.month
valid_monthly_df = df.dropna(subset=["월"]).copy()
valid_monthly_df["월"] = valid_monthly_df["월"].astype(int)

# 꺾은선 그래프 전용 독립 옵션
col_line_scope, col_line_sido = st.columns([1, 1])
with col_line_scope:
    view_mode = st.radio(
        "분석 대상 범위 ",
        options=["전국 전체", "특정 시도", "전국 vs 특정 시도 동시 비교"],
        horizontal=True,
        key="line_view_mode"
    )

with col_line_sido:
    # 전국 전체일 때는 선택이 필요 없음을 시각적으로 알 수 있게 하거나 비활성화 처리
    is_sido_needed = view_mode in ["특정 시도", "전국 vs 특정 시도 동시 비교"]
    selected_sido_line = st.selectbox(
        "조회할 시도 선택 (꺾은선 그래프 전용):",
        options=sido_list,
        index=0,
        disabled=not is_sido_needed,
        key="line_sido_select"
    )

# 1~12월 기본 프레임 생성
all_months = list(range(1, 13))
month_labels = [f"{m}월" for m in all_months]

fig_line = go.Figure()

if view_mode in ["전국 전체", "전국 vs 특정 시도 동시 비교"]:
    nationwide_counts = valid_monthly_df["월"].value_counts().reindex(all_months, fill_value=0)
    fig_line.add_trace(go.Scatter(
        x=month_labels,
        y=nationwide_counts.values,
        mode="lines+markers+text",
        name="전국 전체",
        line=dict(color="#ef4444", width=3),
        marker=dict(size=8, symbol="circle"),
        text=[f"{v:,}건" for v in nationwide_counts.values],
        textposition="top center",
        hovertemplate="<b>전국 전체</b><br>%{x}: <b>%{y:,}건</b><extra></extra>"
    ))

if view_mode in ["특정 시도", "전국 vs 특정 시도 동시 비교"]:
    sido_monthly = valid_monthly_df[valid_monthly_df["시도"] == selected_sido_line]["월"].value_counts().reindex(all_months, fill_value=0)
    
    yaxis_target = "y2" if view_mode == "전국 vs 특정 시도 동시 비교" else "y"
    
    fig_line.add_trace(go.Scatter(
        x=month_labels,
        y=sido_monthly.values,
        mode="lines+markers+text",
        name=selected_sido_line,
        yaxis=yaxis_target,
        line=dict(color="#3b82f6", width=3, dash="solid" if view_mode != "전국 vs 특정 시도 동시 비교" else "dot"),
        marker=dict(size=8, symbol="diamond"),
        text=[f"{v:,}건" for v in sido_monthly.values],
        textposition="bottom center" if view_mode == "전국 vs 특정 시도 동시 비교" else "top center",
        hovertemplate=f"<b>{selected_sido_line}</b><br>%{{x}}: <b>%{{y:,}}건</b><extra></extra>"
    ))

# 타이틀 텍스트 동적 결정
if view_mode == "전국 전체":
    title_text = "<b>2024년 전국 월별 화재 발생 건수 추이</b>"
elif view_mode == "특정 시도":
    title_text = f"<b>2024년 [{selected_sido_line}] 월별 화재 발생 건수 추이</b>"
else:
    title_text = f"<b>2024년 [전국 vs {selected_sido_line}] 월별 화재 발생 건수 동시 비교</b>"

# 레이아웃 구성
layout_kwargs = dict(
    title=dict(
        text=title_text,
        font=dict(size=16)
    ),
    xaxis=dict(
        title="<b>발생 월</b>",
        showgrid=True,
        gridcolor="rgba(128,128,128,0.2)"
    ),
    yaxis=dict(
        title="<b>전국 화재 발생 건수 (건)</b>" if view_mode == "전국 vs 특정 시도 동시 비교" else "<b>화재 발생 건수 (건)</b>",
        showgrid=True,
        gridcolor="rgba(128,128,128,0.2)",
        rangemode="tozero"
    ),
    height=460,
    margin=dict(l=40, r=40, t=60, b=60),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

if view_mode == "전국 vs 특정 시도 동시 비교":
    layout_kwargs["yaxis2"] = dict(
        title=f"<b>{selected_sido_line} 화재건수 (건)</b>",
        overlaying="y",
        side="right",
        showgrid=False,
        rangemode="tozero"
    )

fig_line.update_layout(**layout_kwargs)
st.plotly_chart(fig_line, width="stretch")

# 인사이트 요약
if view_mode == "특정 시도":
    target_series = valid_monthly_df[valid_monthly_df["시도"] == selected_sido_line]["월"].value_counts().reindex(all_months, fill_value=0)
    target_name = selected_sido_line
else:
    target_series = valid_monthly_df["월"].value_counts().reindex(all_months, fill_value=0)
    target_name = "전국"

max_month = target_series.idxmax()
min_month = target_series.idxmin()
avg_month = target_series.mean()

st.caption(
    f" **월별 동향 요약 ({target_name}):** 2024년 {target_name}에서 화재가 가장 많이 발생한 달은 **{max_month}월({target_series[max_month]:,}건)**이며, "
    f"가장 적게 발생한 달은 **{min_month}월({target_series[min_month]:,}건)**입니다. (월평균 **{avg_month:,.0f}건**)"
)

st.markdown("---")
st.subheader(" 발화요인 × 장소대분류 히트맵 분석")

# 분석 옵션 (발화요인 레벨 및 집계 지표 선택)
col_opt1, col_opt2 = st.columns([1, 1])
with col_opt1:
    cause_col = st.radio(
        "발화요인 구분 기준",
        options=["발화요인대분류", "발화요인소분류 (상위 15개)"],
        horizontal=True
    )
with col_opt2:
    metric_choice = st.selectbox(
        "집계 지표 선택",
        options=["화재 발생 건수 (건)", "인명피해 합계 (명)", "재산피해 합계 (천원)"]
    )

# 사용할 데이터프레임 가공
heat_df = df.copy()

if "소분류" in cause_col:
    top_causes = heat_df["발화요인소분류"].value_counts().nlargest(15).index
    heat_df = heat_df[heat_df["발화요인소분류"].isin(top_causes)]
    cause_field = "발화요인소분류"
else:
    cause_field = "발화요인대분류"

place_field = "장소대분류"

# 집계 방식 매핑
if "화재 발생 건수" in metric_choice:
    pivot_table = pd.crosstab(heat_df[cause_field], heat_df[place_field])
    val_suffix = "건"
    colorscale = "YlOrRd"
elif "인명피해" in metric_choice:
    pivot_table = heat_df.pivot_table(
        index=cause_field,
        columns=place_field,
        values="인명피해(명)소계",
        aggfunc="sum",
        fill_value=0
    )
    val_suffix = "명"
    colorscale = "OrRd"
else:
    pivot_table = heat_df.pivot_table(
        index=cause_field,
        columns=place_field,
        values="재산피해소계",
        aggfunc="sum",
        fill_value=0
    )
    val_suffix = "천원"
    colorscale = "Reds"

# 빈도가 높은 순서대로 행/열 정렬 (상위 항목이 위쪽/왼쪽에 오도록)
row_order = pivot_table.sum(axis=1).sort_values(ascending=True).index
col_order = pivot_table.sum(axis=0).sort_values(ascending=False).index
pivot_table = pivot_table.reindex(index=row_order, columns=col_order)

# Plotly 히트맵 생성
fig = go.Figure(data=go.Heatmap(
    z=pivot_table.values,
    x=pivot_table.columns.tolist(),
    y=pivot_table.index.tolist(),
    colorscale=colorscale,
    hoverongaps=False,
    text=pivot_table.values,
    texttemplate="%{text:,}",
    textfont={"size": 11},
    hovertemplate=(
        "<b>장소:</b> %{x}<br>" +
        "<b>발화요인:</b> %{y}<br>" +
        f"<b>{metric_choice.split()[0]}:</b> " + "%{z:,}" + f" {val_suffix}<extra></extra>"
    ),
    colorbar=dict(
        title=dict(text=val_suffix, side="top"),
        tickformat=","
    )
))

fig.update_layout(
    title=dict(
        text=f"<b>[{cause_field} × {place_field}] {metric_choice} 분포 히트맵</b>",
        font=dict(size=16)
    ),
    xaxis=dict(
        title="<b>장소대분류</b>",
        tickangle=-30,
        side="bottom"
    ),
    yaxis=dict(
        title=f"<b>{cause_field}</b>",
        autorange="reversed" # 합계가 가장 큰 항목이 최상단에 오도록 설정
    ),
    height=620,
    margin=dict(l=40, r=40, t=60, b=80),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)"
)

st.plotly_chart(fig, width="stretch")

# 주요 관측 인사이트 요약
top_cell = pivot_table.stack().idxmax()
top_cell_val = pivot_table.stack().max()
st.caption(f" **주요 관측:** 가장 높은 수치를 기록한 조합은 **[{top_cell[0]} × {top_cell[1]}]** (총 **{top_cell_val:,}** {val_suffix}) 입니다.")

