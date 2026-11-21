import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px
import plotly.graph_objects as go

# 페이지 기본 설정
st.set_page_config(
    page_title="2024년 소방청 화재통계 분석 대시보드",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS (KPI 카드 및 스타일링)
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
        line-height: 1.5;
    }
    .card-fire { border-top: 4px solid #ef4444; }
    .card-casualty { border-top: 4px solid #f97316; }
    .card-damage { border-top: 4px solid #eab308; }
    .badge-sub {
        display: inline-block;
        margin-top: 4px;
        padding: 2px 8px;
        border-radius: 4px;
        background-color: rgba(255, 255, 255, 0.08);
        color: #fef08a;
        font-size: 0.8rem;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# 데이터 로드 (캐싱 적용)
@st.cache_data
def load_data():
    file_path = "소방청_연간화재통계_20241231.csv"
    if not os.path.exists(file_path):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, file_path)
    
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


# ==========================================
# 1. 최상단 KPI 메트릭 계산 & 카드 레이아웃
# ==========================================
total_fire_count = len(df)
total_casualties = df["인명피해(명)소계"].sum()
total_deaths = df["사망"].sum()
total_injuries = df["부상"].sum()

# 재산피해(천원 단위 -> 원 단위)
total_property_loss_thousand = df["재산피해소계"].sum()
total_property_loss_won = total_property_loss_thousand * 1000
loss_in_hundred_millions = total_property_loss_won / 100_000_000

# 요청 지표: 100건당 인명피해 인원 & 건당 평균 재산피해액
casualties_per_100 = (total_casualties / total_fire_count * 100) if total_fire_count > 0 else 0
avg_property_loss_won = (total_property_loss_won / total_fire_count) if total_fire_count > 0 else 0
avg_property_loss_manwon = avg_property_loss_won / 10_000

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
        <div class="metric-sub">
            사망 <b>{total_deaths:,}</b>명 &nbsp;|&nbsp; 부상 <b>{total_injuries:,}</b>명<br>
            <span class="badge-sub"> 100건당 인명피해: <b>{casualties_per_100:.2f}명</b></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card card-damage">
        <div class="metric-title">총 재산 피해</div>
        <div class="metric-value">{loss_in_hundred_millions:,.1f} <span style="font-size:1.2rem; font-weight:normal;">억 원</span></div>
        <div class="metric-sub">
            {total_property_loss_thousand:,} 천원 ({total_property_loss_won:,.0f}원)<br>
            <span class="badge-sub">건당 평균 재산피해액: <b>{avg_property_loss_manwon:,.0f}만 원</b> ({avg_property_loss_won:,.0f}원)</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 화재 유형별 건수 · 비중 (막대그래프)
# ==========================================
st.markdown("---")
st.subheader("화재 유형별 발생 건수 및 비중")

fire_type_counts = df["화재유형"].value_counts().reset_index()
fire_type_counts.columns = ["화재유형", "화재건수"]
fire_type_counts["비중(%)"] = (fire_type_counts["화재건수"] / total_fire_count * 100).round(1)

# 가로 막대 그래프 (텍스트 가독성 최적화)
fig_type = px.bar(
    fire_type_counts.sort_values(by="화재건수", ascending=True),
    x="화재건수",
    y="화재유형",
    orientation="h",
    text=fire_type_counts.sort_values(by="화재건수", ascending=True).apply(
        lambda r: f"{r['화재건수']:,}건 ({r['비중(%)']}%)", axis=1
    ),
    color="화재건수",
    color_continuous_scale="Reds",
    hover_data={"화재유형": True, "화재건수": ":,", "비중(%)": ":.1f%"},
    labels={"화재유형": "화재 유형", "화재건수": "화재 발생 건수 (건)"}
)

fig_type.update_traces(
    textposition="outside",
    cliponaxis=False
)

fig_type.update_layout(
    height=340,
    xaxis=dict(title="<b>화재 발생 건수 (건)</b>"),
    yaxis=dict(title="<b>화재 유형</b>"),
    coloraxis_showscale=False,
    margin=dict(l=40, r=60, t=30, b=40),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)"
)

st.plotly_chart(fig_type, width="stretch")

top_type = fire_type_counts.iloc[0]
st.caption(
    f"**화재 유형 분석 요약:** 2024년 화재 중 **[{top_type['화재유형']}]**이 "
    f"총 **{top_type['화재건수']:,}건({top_type['비중(%)']}%)**으로 가장 큰 비중을 차지했습니다."
)

# ==========================================
# 3. 시도별 · 시군구 화재 발생 건수 분석
# ==========================================
st.markdown("---")
st.subheader("📍 시도별 · 시군구 화재 발생 건수 분석")

sido_list = df["시도"].value_counts().index.tolist()

col_sido_sel, col_sido_sort = st.columns([2, 1])
with col_sido_sel:
    selected_sido_bar = st.selectbox("분석할 시도를 선택하세요 (막대그래프 전용):", options=sido_list, index=0, key="bar_sido_select")
with col_sido_sort:
    sort_order = st.radio("시군구 정렬 기준", options=["화재건수 많은 순", "시군구 이름순"], horizontal=True, key="bar_sort_order")

sido_df = df[df["시도"] == selected_sido_bar]
sigungu_counts = sido_df["시_군_구"].value_counts().reset_index()
sigungu_counts.columns = ["시_군_구", "화재건수"]

if sort_order == "화재건수 많은 순":
    sigungu_counts = sigungu_counts.sort_values(by="화재건수", ascending=False)
else:
    sigungu_counts = sigungu_counts.sort_values(by="시_군_구", ascending=True)

sigungu_counts["비중(%)"] = (sigungu_counts["화재건수"] / len(sido_df) * 100).round(1)

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
    height=460,
    margin=dict(l=40, r=40, t=60, b=80),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)"
)

st.plotly_chart(fig_bar, width="stretch")

top_sigungu = sigungu_counts.iloc[0] if not sigungu_counts.empty else None
if top_sigungu is not None:
    st.caption(f" **{selected_sido_bar} 1위 발생 지역:** **{top_sigungu['시_군_구']}** ({top_sigungu['화재건수']:,}건, {selected_sido_bar} 전체의 {top_sigungu['비중(%)']}%)")

# ==========================================
# 4. 월별 화재 발생 추이 (꺾은선 그래프)
# ==========================================
st.markdown("---")
st.subheader("📈 월별 화재 발생 추이 (2024년)")

df["월"] = df["일시"].dt.month
valid_monthly_df = df.dropna(subset=["월"]).copy()
valid_monthly_df["월"] = valid_monthly_df["월"].astype(int)

col_line_scope, col_line_sido = st.columns([1, 1])
with col_line_scope:
    view_mode = st.radio(
        "분석 대상 범위 (꺾은선 그래프 전용)",
        options=["전국 전체", "특정 시도", "전국 vs 특정 시도 동시 비교"],
        horizontal=True,
        key="line_view_mode"
    )

with col_line_sido:
    is_sido_needed = view_mode in ["특정 시도", "전국 vs 특정 시도 동시 비교"]
    selected_sido_line = st.selectbox(
        "조회할 시도 선택 (꺾은선 그래프 전용):",
        options=sido_list,
        index=0,
        disabled=not is_sido_needed,
        key="line_sido_select"
    )

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

if view_mode == "전국 전체":
    title_text = "<b>2024년 전국 월별 화재 발생 건수 추이</b>"
elif view_mode == "특정 시도":
    title_text = f"<b>2024년 [{selected_sido_line}] 월별 화재 발생 건수 추이</b>"
else:
    title_text = f"<b>2024년 [전국 vs {selected_sido_line}] 월별 화재 발생 건수 동시 비교</b>"

layout_kwargs = dict(
    title=dict(text=title_text, font=dict(size=16)),
    xaxis=dict(title="<b>발생 월</b>", showgrid=True, gridcolor="rgba(128,128,128,0.2)"),
    yaxis=dict(
        title="<b>전국 화재 발생 건수 (건)</b>" if view_mode == "전국 vs 특정 시도 동시 비교" else "<b>화재 발생 건수 (건)</b>",
        showgrid=True,
        gridcolor="rgba(128,128,128,0.2)",
        rangemode="tozero"
    ),
    height=440,
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

# =========================================================================
# 5. 장소별 발생·피해현황: 대분류 선택 시 중·소분류 단계적 탐색 막대그래프
# =========================================================================
st.markdown("---")
st.subheader(" 장소별 발생·피해 현황 계층 분석 (대분류 → 중·소분류)")

col_place_opt1, col_place_opt2 = st.columns([1, 1])
with col_place_opt1:
    place_metric = st.selectbox(
        "분석 지표 선택",
        options=["화재 발생 건수 (건)", "인명피해 합계 (명)", "재산피해 합계 (천원)"],
        key="place_metric_select"
    )

major_places = df["장소대분류"].value_counts().index.tolist()
with col_place_opt2:
    selected_major_place = st.selectbox(
        "1단계: 장소 대분류 선택",
        options=major_places,
        index=0,
        key="major_place_select"
    )

# 1단계 대분류 필터링
major_filtered_df = df[df["장소대분류"] == selected_major_place]

# 지표 매핑 함수
def aggregate_place(data, group_col, metric_name):
    if "건수" in metric_name:
        res = data[group_col].value_counts().reset_index()
        res.columns = [group_col, "값"]
        unit = "건"
    elif "인명피해" in metric_name:
        res = data.groupby(group_col)["인명피해(명)소계"].sum().reset_index()
        res.columns = [group_col, "값"]
        unit = "명"
    else:
        res = data.groupby(group_col)["재산피해소계"].sum().reset_index()
        res.columns = [group_col, "값"]
        unit = "천원"
    res = res.sort_values(by="값", ascending=False)
    total_val = res["값"].sum()
    res["비중(%)"] = (res["값"] / total_val * 100).round(1) if total_val > 0 else 0
    return res, unit

mid_agg, place_unit = aggregate_place(major_filtered_df, "장소중분류", place_metric)

# 1단계: 중분류 막대그래프
fig_mid = px.bar(
    mid_agg,
    x="장소중분류",
    y="값",
    text="값",
    color="값",
    color_continuous_scale="Blues",
    title=f"<b>[1단계: {selected_major_place}] 장소 중분류별 {place_metric} (총 {len(mid_agg)}개 중분류)</b>",
    labels={"장소중분류": "장소 중분류", "값": place_metric},
    hover_data={"장소중분류": True, "값": ":,", "비중(%)": ":.1f%"}
)
fig_mid.update_traces(
    texttemplate="%{text:,}" + place_unit,
    textposition="outside",
    cliponaxis=False
)
fig_mid.update_layout(
    height=420,
    xaxis_tickangle=-30,
    xaxis=dict(title="<b>장소 중분류</b>"),
    yaxis=dict(title=f"<b>{place_metric}</b>"),
    coloraxis_showscale=False,
    margin=dict(l=40, r=40, t=60, b=70),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)"
)
st.plotly_chart(fig_mid, width="stretch")

# 2단계: 중분류 선택 후 소분류 상세 조회 (Drill-down)
mid_choices = mid_agg["장소중분류"].tolist()
selected_mid_place = st.selectbox(
    f"2단계: [{selected_major_place}] 내 세부 중분류를 선택하여 소분류 확인:",
    options=mid_choices,
    index=0,
    key="mid_place_select"
)

sub_filtered_df = major_filtered_df[major_filtered_df["장소중분류"] == selected_mid_place]
sub_agg, sub_unit = aggregate_place(sub_filtered_df, "장소소분류", place_metric)

fig_sub = px.bar(
    sub_agg,
    x="장소소분류",
    y="값",
    text="값",
    color="값",
    color_continuous_scale="Teal",
    title=f"<b>[2단계: {selected_major_place} > {selected_mid_place}] 소분류별 {place_metric} (총 {len(sub_agg)}개 소분류)</b>",
    labels={"장소소분류": "장소 소분류", "값": place_metric},
    hover_data={"장소소분류": True, "값": ":,", "비중(%)": ":.1f%"}
)
fig_sub.update_traces(
    texttemplate="%{text:,}" + sub_unit,
    textposition="outside",
    cliponaxis=False
)
fig_sub.update_layout(
    height=420,
    xaxis_tickangle=-30,
    xaxis=dict(title="<b>장소 소분류</b>"),
    yaxis=dict(title=f"<b>{place_metric}</b>"),
    coloraxis_showscale=False,
    margin=dict(l=40, r=40, t=60, b=70),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)"
)
st.plotly_chart(fig_sub, width="stretch")

if not sub_agg.empty:
    top_sub = sub_agg.iloc[0]
    st.caption(
        f" **계층 분석 인사이트:** [{selected_major_place} > {selected_mid_place}] 내에서 "
        f"가장 높은 수치를 기록한 소분류는 **'{top_sub['장소소분류']}'** ({top_sub['값']:,}{sub_unit}, 비중 {top_sub['비중(%)']}%)입니다."
    )

# =========================================================================
# 6. 화재 유형 · 장소별 피해 수준 비교 (막대그래프)
# =========================================================================
st.markdown("---")
st.subheader(" 화재 유형 · 장소별 피해 수준 비교")

col_cmp_opt1, col_cmp_opt2 = st.columns([1, 1])
with col_cmp_opt1:
    compare_metric_choice = st.selectbox(
        "비교 피해 지표 선택",
        options=[
            "건당 평균 재산피해액 (만원)",
            "건당 평균 인명피해 (명)",
            "총 재산피해액 (억원)",
            "총 인명피해 (명)",
            "화재 발생 건수 (건)"
        ],
        key="compare_metric_select"
    )

with col_cmp_opt2:
    default_majors = ["주거", "산업시설", "자동차,철도차량", "생활서비스", "판매,업무시설"]
    selected_compare_places = st.multiselect(
        "비교 대상 장소 대분류 선택",
        options=major_places,
        default=[p for p in default_majors if p in major_places],
        key="compare_places_multiselect"
    )

if not selected_compare_places:
    st.warning("비교할 장소 대분류를 최소 1개 이상 선택해 주세요.")
else:
    cmp_filtered = df[df["장소대분류"].isin(selected_compare_places)]
    
    # 그룹바이 피벗 집계
    grouped_cmp = cmp_filtered.groupby(["화재유형", "장소대분류"]).agg(
        화재건수=("일시", "count"),
        인명피해=("인명피해(명)소계", "sum"),
        재산피해_천원=("재산피해소계", "sum")
    ).reset_index()
    
    grouped_cmp["건당_재산피해_만원"] = (grouped_cmp["재산피해_천원"] * 1000 / grouped_cmp["화재건수"] / 10_000).round(1)
    grouped_cmp["건당_인명피해_명"] = (grouped_cmp["인명피해"] / grouped_cmp["화재건수"]).round(3)
    grouped_cmp["총_재산피해_억원"] = (grouped_cmp["재산피해_천원"] * 1000 / 100_000_000).round(2)
    
    # 선택 지표 매핑
    if "건당 평균 재산피해액" in compare_metric_choice:
        y_col = "건당_재산피해_만원"
        val_format = ":,.1f"
        suffix = "만원"
    elif "건당 평균 인명피해" in compare_metric_choice:
        y_col = "건당_인명피해_명"
        val_format = ":.3f"
        suffix = "명"
    elif "총 재산피해액" in compare_metric_choice:
        y_col = "총_재산피해_억원"
        val_format = ":,.2f"
        suffix = "억원"
    elif "총 인명피해" in compare_metric_choice:
        y_col = "인명피해"
        val_format = ":,"
        suffix = "명"
    else:
        y_col = "화재건수"
        val_format = ":,"
        suffix = "건"
    
    fig_cmp = px.bar(
        grouped_cmp,
        x="화재유형",
        y=y_col,
        color="장소대분류",
        barmode="group",
        title=f"<b>화재 유형 및 장소별 [{compare_metric_choice}] 그룹 비교</b>",
        labels={"화재유형": "화재 유형", y_col: compare_metric_choice, "장소대분류": "장소 대분류"},
        hover_data={"화재유형": True, "장소대분류": True, y_col: val_format}
    )
    
    fig_cmp.update_layout(
        height=480,
        xaxis_tickangle=-15,
        xaxis=dict(title="<b>화재 유형</b>"),
        yaxis=dict(title=f"<b>{compare_metric_choice}</b>"),
        legend=dict(title="장소 대분류", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=70, b=60),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    
    st.plotly_chart(fig_cmp, width="stretch")
    
    # 최고 피해 조합 관측
    if not grouped_cmp.empty:
        max_idx = grouped_cmp[y_col].idxmax()
        top_row = grouped_cmp.loc[max_idx]
        st.caption(
            f"**피해 수준 비교 인사이트:** [{compare_metric_choice}] 기준 가장 높은 수치를 기록한 조합은 "
            f"**'{top_row['화재유형']} × {top_row['장소대분류']}'** ({top_row[y_col]:,}{suffix}) 입니다."
        )

# ==========================================
# 7. 발화요인 × 장소대분류 히트맵 분석
# ==========================================
st.markdown("---")
st.subheader("발화요인 × 장소대분류 히트맵 분석")

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

heat_df = df.copy()

if "소분류" in cause_col:
    top_causes = heat_df["발화요인소분류"].value_counts().nlargest(15).index
    heat_df = heat_df[heat_df["발화요인소분류"].isin(top_causes)]
    cause_field = "발화요인소분류"
else:
    cause_field = "발화요인대분류"

place_field = "장소대분류"

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

row_order = pivot_table.sum(axis=1).sort_values(ascending=True).index
col_order = pivot_table.sum(axis=0).sort_values(ascending=False).index
pivot_table = pivot_table.reindex(index=row_order, columns=col_order)

fig_heat = go.Figure(data=go.Heatmap(
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

fig_heat.update_layout(
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
        autorange="reversed"
    ),
    height=620,
    margin=dict(l=40, r=40, t=60, b=80),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)"
)

st.plotly_chart(fig_heat, width="stretch")

top_cell = pivot_table.stack().idxmax()
top_cell_val = pivot_table.stack().max()
st.caption(f" **주요 관측:** 가장 높은 수치를 기록한 조합은 **[{top_cell[0]} × {top_cell[1]}]** (총 **{top_cell_val:,}** {val_suffix}) 입니다.")
