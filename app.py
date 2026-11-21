import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 페이지 기본 설정
# ==========================================
st.set_page_config(
    page_title="2024년 소방청 화재통계 분석 대시보드",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 커스텀 CSS (Streamlit 다크모드/라이트모드 100% 자동 반응)
# ==========================================
st.markdown("""
<style>
    /* 상단 수치 카드 (Streamlit 시스템 테마 변수 연동) */
    .metric-card {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 12px;
        padding: 20px 22px;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.06);
        margin-bottom: 8px;
    }
    .metric-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: var(--text-color);
        opacity: 0.85;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 2.1rem;
        font-weight: 800;
        color: var(--text-color);
        letter-spacing: -0.02em;
        line-height: 1.2;
    }
    .metric-sub {
        font-size: 0.88rem;
        color: var(--text-color);
        opacity: 0.9;
        margin-top: 8px;
        line-height: 1.5;
    }
    .card-fire { border-top: 4px solid #ef4444; }
    .card-casualty { border-top: 4px solid #f97316; }
    .card-damage { border-top: 4px solid #eab308; }
    
    .badge-sub {
        display: inline-block;
        margin-top: 5px;
        padding: 3px 8px;
        border-radius: 4px;
        background-color: rgba(128, 128, 128, 0.15);
        color: var(--text-color);
        font-size: 0.82rem;
        font-weight: 600;
    }

    /* 탭 헤더 스타일 (테마 연동) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 16px;
        margin-top: 1rem;
        margin-bottom: 1.2rem;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 1.05rem;
        font-weight: 700;
        padding: 10px 18px;
        color: var(--text-color);
        opacity: 0.75;
    }
    .stTabs [aria-selected="true"] {
        color: #ef4444 !important;
        opacity: 1.0 !important;
        border-bottom: 3px solid #ef4444 !important;
    }

    /* 도표 제목용 섹션 헤더 (테마 연동) */
    .chart-section-title {
        font-size: 1.15rem;
        font-weight: 800;
        color: var(--text-color);
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 데이터 로드 (캐싱)
# ==========================================
@st.cache_data
def load_data():
    file_path = "소방청_연간화재통계_20241231.csv"
    if not os.path.exists(file_path):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, file_path)
    
    df = pd.read_csv(file_path, encoding="cp949")
    if "일시" in df.columns:
        df["일시"] = pd.to_datetime(df["일시"], errors="coerce")
        df["월"] = df["일시"].dt.month
        df["시간대"] = df["일시"].dt.hour
        days_kr = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
        df["요일"] = df["일시"].dt.weekday.map(lambda x: days_kr[int(x)] if pd.notnull(x) else None)
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# ==========================================
# 금액 단위 변환 헬퍼 함수 (한국어 억/만/천 원)
# ==========================================
def format_korean_money(val_thousand):
    val_won = val_thousand * 1000
    if abs(val_won) >= 100_000_000:
        return f"{val_won / 100_000_000:,.1f}억"
    elif abs(val_won) >= 10_000_000:
        return f"{val_won / 10_000_000:,.1f}천만"
    elif abs(val_won) >= 10_000:
        return f"{val_won / 10_000:,.0f}만"
    else:
        return f"{val_thousand:,}천"

# ==========================================
# 상단 타이틀
# ==========================================
st.title("2024년 소방청 전국 화재통계 분석 대시보드")
st.caption("데이터 출처: 소방청 국가화재정보시스템 (2024년 1월 1일 ~ 12월 31일)")

# 사이드바
with st.sidebar:
    st.header("데이터 필터 및 설정")
    
    # 발화요인 '미상' 제외 온/오프 토글 버튼
    exclude_unknown = st.toggle(
        "발화요인 '미상' 데이터 제외",
        value=False,
        help="발화요인이 '미상'으로 분류된 화재 데이터(약 3,051건)를 분석 대상에서 제외합니다."
    )
    
    if exclude_unknown:
        df = df[df["발화요인대분류"] != "미상"]
        st.warning(f" **'미상' 제외 적용 중**\n\n분석 데이터: **{len(df):,}건**")
    else:
        st.success(f" **전체 데이터 분석 중**\n\n총 데이터: **{len(df):,}건**")
        
    st.markdown("---")
    st.info("상단 탭을 클릭하여 시공간 패턴, 장소·피해 심각도, 발화요인별 분석을 나누어 확인하실 수 있습니다.")

# ==========================================
# 상단 수치 카드 (원래 위치 3열 배치, 글씨 짤림 없음)
# ==========================================
total_fire_count = len(df)
total_casualties = df["인명피해(명)소계"].sum()
total_deaths = df["사망"].sum()
total_injuries = df["부상"].sum()

total_property_loss_thousand = df["재산피해소계"].sum()
total_property_loss_won = total_property_loss_thousand * 1000
loss_in_hundred_millions = total_property_loss_won / 100_000_000

casualties_per_100 = (total_casualties / total_fire_count * 100) if total_fire_count > 0 else 0
avg_property_loss_won = (total_property_loss_won / total_fire_count) if total_fire_count > 0 else 0
avg_property_loss_manwon = avg_property_loss_won / 10_000

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div class="metric-card card-fire">
        <div class="metric-title">총 화재 건수</div>
        <div class="metric-value">{total_fire_count:,} <span style="font-size:1.2rem; font-weight:normal; opacity:0.75;">건</span></div>
        <div class="metric-sub">2024년 연간 누적 화재 발생 건수</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card card-casualty">
        <div class="metric-title">총 인명 피해</div>
        <div class="metric-value">{total_casualties:,} <span style="font-size:1.2rem; font-weight:normal; opacity:0.75;">명</span></div>
        <div class="metric-sub">
            사망 <b>{total_deaths:,}</b>명 &nbsp;|&nbsp; 부상 <b>{total_injuries:,}</b>명<br>
            <span class="badge-sub"> 100건당 인명피해: <b>{casualties_per_100:.2f}명</b></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card card-damage">
        <div class="metric-title"> 총 재산 피해</div>
        <div class="metric-value">{loss_in_hundred_millions:,.1f} <span style="font-size:1.2rem; font-weight:normal; opacity:0.75;">억 원</span></div>
        <div class="metric-sub">
            {total_property_loss_thousand:,} 천원 ({total_property_loss_won:,.0f}원)<br>
            <span class="badge-sub"> 건당 평균 피해액: <b>{avg_property_loss_manwon:,.0f}만 원</b> ({avg_property_loss_won:,.0f}원)</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 공통 도표 스타일 템플릿 (Streamlit 다크/라이트 테마 자동 연동)
def apply_chart_theme(fig, title_text, height=450):
    fig.update_layout(
        title=dict(
            text=f"<b>{title_text}</b>",
            font=dict(size=16),
            x=0,
            xanchor="left"
        ),
        height=height,
        margin=dict(l=40, r=30, t=55, b=60),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    fig.update_xaxes(
        title_font=dict(size=12),
        tickfont=dict(size=11),
        gridcolor="rgba(128,128,128,0.15)"
    )
    fig.update_yaxes(
        title_font=dict(size=12),
        tickfont=dict(size=11),
        gridcolor="rgba(128,128,128,0.15)"
    )
    return fig

# ==========================================
# 탭 형식 구성 (3개 탭)
# ==========================================
st.markdown("---")
tab1, tab2, tab3 = st.tabs([
    " 시공간 패턴 분석",
    " 장소 · 피해 심각도 분석",
    " 발화요인 심층 분석"
])

# ----------------------------------------------------
# TAB 1: 시공간 패턴 분석
# ----------------------------------------------------
with tab1:
    # 1. 화재 유형별 건수·비중
    st.markdown("<div class='chart-section-title'>1. 화재 유형별 발생 건수 및 비중</div>", unsafe_allow_html=True)
    fire_type_counts = df["화재유형"].value_counts().reset_index()
    fire_type_counts.columns = ["화재유형", "화재건수"]
    fire_type_counts["비중(%)"] = (fire_type_counts["화재건수"] / total_fire_count * 100).round(1)

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
        labels={"화재유형": "화재 유형", "화재건수": "화재 발생 건수 (건)"}
    )
    fig_type.update_traces(textposition="outside", cliponaxis=False)
    apply_chart_theme(fig_type, "화재 유형별 발생 건수 및 비중 (2024년)", height=320)
    fig_type.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig_type, width="stretch")

    st.markdown("---")

    # 2열 분할 레이아웃: 좌(시도/시군구 막대 + 월별 추이) / 우(요일-시간 히트맵)
    col_t1_left, col_t1_right = st.columns([1.1, 1], gap="medium")

    with col_t1_left:
        # 2. 시도별 · 시군구 막대그래프
        st.markdown("<div class='chart-section-title'>2. 시도별 · 시군구 화재 발생 건수</div>", unsafe_allow_html=True)
        sido_list = df["시도"].value_counts().index.tolist()
        
        c_sel1, c_sel2 = st.columns([1.5, 1])
        with c_sel1:
            selected_sido_bar = st.selectbox("분석할 시도 선택 (시군구 도표):", options=sido_list, index=0, key="t1_bar_sido_select")
        with c_sel2:
            sort_order = st.radio("정렬 기준", ["화재건수순", "이름순"], horizontal=True, key="t1_sort_order")

        sido_df = df[df["시도"] == selected_sido_bar]
        sigungu_counts = sido_df["시_군_구"].value_counts().reset_index()
        sigungu_counts.columns = ["시_군_구", "화재건수"]

        if sort_order == "화재건수순":
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
            labels={"시_군_구": "시·군·구", "화재건수": "건수"},
            hover_data={"시_군_구": True, "화재건수": ":,", "비중(%)": ":.1f%"}
        )
        fig_bar.update_traces(texttemplate="%{text:,}건", textposition="outside", cliponaxis=False)
        apply_chart_theme(fig_bar, f"[{selected_sido_bar}] 시·군·구별 화재 발생 건수 (총 {len(sido_df):,}건)", height=420)
        fig_bar.update_layout(xaxis_tickangle=-35, coloraxis_showscale=False)
        st.plotly_chart(fig_bar, width="stretch")

        # 3. 월별 화재 발생 추이 (독립적인 시도 선택 옵션)
        st.markdown("<div class='chart-section-title' style='margin-top:20px;'>3. 월별 화재 발생 추이 (2024년)</div>", unsafe_allow_html=True)
        
        c_line1, c_line2 = st.columns([1.2, 1.3])
        with c_line1:
            line_scope = st.radio("분석 범위 (월별 도표):", ["전국 전체", "특정 시도"], horizontal=True, key="t1_line_scope")
        with c_line2:
            selected_sido_line = st.selectbox(
                "월별 분석 시도 선택:",
                options=sido_list,
                index=0,
                disabled=(line_scope == "전국 전체"),
                key="t1_line_sido_select"
            )
        
        if line_scope == "전국 전체":
            target_df = df
            line_chart_title = "2024년 전국 월별 화재 발생 추이"
        else:
            target_df = df[df["시도"] == selected_sido_line]
            line_chart_title = f"2024년 [{selected_sido_line}] 월별 화재 발생 추이"

        all_months = list(range(1, 13))
        month_labels = [f"{m}월" for m in all_months]
        month_counts = target_df["월"].value_counts().reindex(all_months, fill_value=0)

        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(
            x=month_labels,
            y=month_counts.values,
            mode="lines+markers+text",
            text=[f"{v:,}건" for v in month_counts.values],
            textposition="top center",
            line=dict(color="#ef4444", width=3),
            marker=dict(size=7, color="#ef4444"),
            hovertemplate="%{x}: <b>%{y:,}건</b><extra></extra>"
        ))
        apply_chart_theme(fig_line, line_chart_title, height=380)
        st.plotly_chart(fig_line, width="stretch")

    with col_t1_right:
        # 4. 요일 × 시간대별 화재 발생 건수 히트맵
        st.markdown("<div class='chart-section-title'>4. 요일 · 시간대별 화재 발생 건수 히트맵</div>", unsafe_allow_html=True)
        
        days_kr = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
        hours_list = list(range(24))
        hours_labels = [f"{h:02d}시" for h in hours_list]

        ct_day_hour = pd.crosstab(df["요일"], df["시간대"]).reindex(index=days_kr, columns=hours_list, fill_value=0)

        # 상위 75% 이상(상위 25% 고밀도 구간)은 흰색(#ffffff), 그 외에는 검정색(#000000)으로 표시하는 annotations 구성
        q75_time = np.percentile(ct_day_hour.values, 75)
        annotations_time = []
        for r_name in ct_day_hour.index:
            for c_idx, c_label in enumerate(hours_labels):
                val = ct_day_hour.loc[r_name, c_idx]
                text_color = "#ffffff" if val >= q75_time else "#000000"
                annotations_time.append(dict(
                    x=c_label,
                    y=r_name,
                    text=f"{val:,}",
                    showarrow=False,
                    font=dict(size=9.5, color=text_color, family="sans-serif")
                ))

        fig_day_hour = go.Figure(data=go.Heatmap(
            z=ct_day_hour.values,
            x=hours_labels,
            y=days_kr,
            colorscale="YlOrRd",
            hoverongaps=False,
            hovertemplate="<b>%{y} %{x}</b><br>화재 건수: <b>%{z:,}건</b><extra></extra>",
            colorbar=dict(title=dict(text="건수"))
        ))
        apply_chart_theme(fig_day_hour, "요일 및 시간대별 화재 발생 건수 분포 (전국)", height=560)
        fig_day_hour.update_layout(
            annotations=annotations_time,
            xaxis=dict(tickangle=-45, title="<b>발생 시간대 (00시 ~ 23시)</b>"),
            yaxis=dict(autorange="reversed", title="<b>요일</b>")
        )
        st.plotly_chart(fig_day_hour, width="stretch")

        # 주요 관측 요약 카드
        max_time_cell = ct_day_hour.stack().idxmax()
        max_time_val = ct_day_hour.stack().max()
        top_sigungu = sigungu_counts.iloc[0] if not sigungu_counts.empty else None
        
        st.info(f"""
         **시공간 주요 관측 요약 (Key Insights)**
        - **피크 시간대:** 화재가 가장 빈번한 시간대는 **{max_time_cell[0]} {max_time_cell[1]:02d}시 ({max_time_val:,}건)**이며, 주로 낮 11시 ~ 16시에 집중됩니다.
        - **지역 집중도:** 선택하신 **{selected_sido_bar}**에서는 **{top_sigungu['시_군_구']}**({top_sigungu['화재건수']:,}건, {top_sigungu['비중(%)']}%)가 가장 많았습니다.
        - **시기별 특징:** 3월(3,668건)과 12월(3,587건)에 연간 화재 발생률이 가장 높게 나타났습니다.
        """)

# ----------------------------------------------------
# TAB 2: 장소 · 피해 심각도 분석
# ----------------------------------------------------
with tab2:
    st.markdown("<div class='chart-section-title'> 장소별 발생·피해 현황 및 심각도 분석</div>", unsafe_allow_html=True)
    
    col_t2_left, col_t2_right = st.columns([1.1, 1], gap="medium")

    with col_t2_left:
        st.subheader("1. 장소 계층 분석 (대분류 → 중·소분류 단계적 탐색)")
        
        p_opt1, p_opt2 = st.columns([1, 1])
        with p_opt1:
            place_metric = st.selectbox(
                "분석 지표 선택",
                ["화재 발생 건수 (건)", "인명피해 합계 (명)", "재산피해 합계 (천원)"],
                key="t2_place_metric"
            )
        with p_opt2:
            major_places = df["장소대분류"].value_counts().index.tolist()
            selected_major = st.selectbox("1단계: 장소 대분류 선택", major_places, index=0, key="t2_major_select")

        major_df = df[df["장소대분류"] == selected_major]

        def get_place_agg(data, col, metric):
            if "건수" in metric:
                res = data[col].value_counts().reset_index()
                res.columns = [col, "값"]
                unit = "건"
            elif "인명피해" in metric:
                res = data.groupby(col)["인명피해(명)소계"].sum().reset_index()
                res.columns = [col, "값"]
                unit = "명"
            else:
                res = data.groupby(col)["재산피해소계"].sum().reset_index()
                res.columns = [col, "값"]
                unit = "천원"
            res = res.sort_values(by="값", ascending=False)
            return res, unit

        # 중분류 막대그래프
        mid_agg, p_unit = get_place_agg(major_df, "장소중분류", place_metric)
        fig_mid = px.bar(
            mid_agg,
            x="장소중분류",
            y="값",
            text="값",
            color="값",
            color_continuous_scale="Blues",
            labels={"장소중분류": "장소 중분류", "값": place_metric}
        )
        fig_mid.update_traces(texttemplate="%{text:,}" + p_unit, textposition="outside", cliponaxis=False)
        apply_chart_theme(fig_mid, f"[1단계: {selected_major}] 중분류별 {place_metric}", height=380)
        fig_mid.update_layout(xaxis_tickangle=-30, coloraxis_showscale=False)
        st.plotly_chart(fig_mid, width="stretch")

        # 2단계: 소분류 막대그래프 (Drill-down)
        mid_options = mid_agg["장소중분류"].tolist()
        selected_mid = st.selectbox(f"2단계: [{selected_major}] 내 중분류 선택 (소분류 상세 조회):", mid_options, index=0, key="t2_mid_select")

        sub_df = major_df[major_df["장소중분류"] == selected_mid]
        sub_agg, s_unit = get_place_agg(sub_df, "장소소분류", place_metric)

        fig_sub = px.bar(
            sub_agg,
            x="장소소분류",
            y="값",
            text="값",
            color="값",
            color_continuous_scale="Teal",
            labels={"장소소분류": "장소 소분류", "값": place_metric}
        )
        fig_sub.update_traces(texttemplate="%{text:,}" + s_unit, textposition="outside", cliponaxis=False)
        apply_chart_theme(fig_sub, f"[2단계: {selected_major} > {selected_mid}] 소분류별 {place_metric}", height=380)
        fig_sub.update_layout(xaxis_tickangle=-30, coloraxis_showscale=False)
        st.plotly_chart(fig_sub, width="stretch")

    with col_t2_right:
        st.subheader("2. 화재 유형 · 장소별 피해 수준 비교")
        
        cmp_metric = st.selectbox(
            "비교 피해 지표 선택",
            ["건당 평균 재산피해액 (만원)", "건당 평균 인명피해 (명)", "총 재산피해액 (억원)", "총 인명피해 (명)", "화재 발생 건수 (건)"],
            key="t2_cmp_metric"
        )
        
        # 특정 분야(산업시설 등) 피해금액 집중 시 격차를 보정하기 위한 로그 스케일 옵션
        is_money_metric = "재산피해" in cmp_metric
        col_cmp_sub1, col_cmp_sub2 = st.columns([1.5, 1])
        with col_cmp_sub1:
            target_places = st.multiselect(
                "비교 대상 장소 대분류 선택",
                options=major_places,
                default=["주거", "산업시설", "자동차,철도차량", "생활서비스", "판매,업무시설"],
                key="t2_places_multi"
            )
        with col_cmp_sub2:
            use_log_bar = st.checkbox(
                "로그 스케일 (Log Scale) 축 적용",
                value=is_money_metric,
                help="특정 장소의 압도적인 피해금액으로 인해 다른 장소의 수치가 묻히는 현상을 보정하여 고르게 비교합니다.",
                key="t2_log_bar_chk"
            )

        if target_places:
            cmp_df = df[df["장소대분류"].isin(target_places)]
            grouped_cmp = cmp_df.groupby(["화재유형", "장소대분류"]).agg(
                건수=("일시", "count"),
                인명피해=("인명피해(명)소계", "sum"),
                재산피해_천원=("재산피해소계", "sum")
            ).reset_index()

            grouped_cmp["건당_재산피해_만원"] = (grouped_cmp["재산피해_천원"] * 1000 / grouped_cmp["건수"] / 10_000).round(1)
            grouped_cmp["건당_인명피해_명"] = (grouped_cmp["인명피해"] / grouped_cmp["건수"]).round(3)
            grouped_cmp["총_재산피해_억원"] = (grouped_cmp["재산피해_천원"] * 1000 / 100_000_000).round(2)

            if "건당 평균 재산피해액" in cmp_metric:
                y_field, fmt, text_tmpl = "건당_재산피해_만원", ":,.1f만원", "%{y:,.0f}만"
            elif "건당 평균 인명피해" in cmp_metric:
                y_field, fmt, text_tmpl = "건당_인명피해_명", ":.3f명", "%{y:.2f}명"
            elif "총 재산피해액" in cmp_metric:
                y_field, fmt, text_tmpl = "총_재산피해_억원", ":,.2f억원", "%{y:,.1f}억"
            elif "총 인명피해" in cmp_metric:
                y_field, fmt, text_tmpl = "인명피해", ":,명", "%{y:,}명"
            else:
                y_field, fmt, text_tmpl = "건수", ":,건", "%{y:,}건"

            fig_cmp = px.bar(
                grouped_cmp,
                x="화재유형",
                y=y_field,
                text=y_field,
                color="장소대분류",
                barmode="group",
                labels={"화재유형": "화재 유형", y_field: cmp_metric, "장소대분류": "장소 대분류"},
                hover_data={"화재유형": True, "장소대분류": True, y_field: fmt}
            )
            fig_cmp.update_traces(
                texttemplate=text_tmpl,
                textposition="outside",
                textfont=dict(size=9),
                cliponaxis=False
            )
            apply_chart_theme(fig_cmp, f"화재 유형 × 장소 대분류 [{cmp_metric}] 비교", height=580)
            if use_log_bar:
                fig_cmp.update_yaxes(type="log", title=f"<b>{cmp_metric} (로그 스케일)</b>")
            fig_cmp.update_layout(
                xaxis_tickangle=-15,
                legend=dict(title=dict(text="<b>장소 대분류</b>"), orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_cmp, width="stretch")

            top_cmp = grouped_cmp.loc[grouped_cmp[y_field].idxmax()]
            st.info(f" **심각도 인사이트:** [{cmp_metric}] 기준 가장 높은 수치를 기록한 조합은 **'{top_cmp['화재유형']} × {top_cmp['장소대분류']}'** (수치: **{top_cmp[y_field]:,}**) 입니다.")
        else:
            st.warning("비교할 장소 대분류를 최소 1개 이상 선택해 주세요.")

# ----------------------------------------------------
# TAB 3: 발화요인 심층 분석
# ----------------------------------------------------
with tab3:
    st.markdown("<div class='chart-section-title'> 발화요인 × 장소대분류 크로스탭 히트맵 심층 분석</div>", unsafe_allow_html=True)
    
    t3_col1, t3_col2 = st.columns([1, 1])
    with t3_col1:
        cause_level = st.radio("발화요인 분류 기준", ["발화요인대분류", "발화요인소분류 (상위 15개)"], horizontal=True, key="t3_cause_radio")
    with t3_col2:
        heat_metric = st.selectbox("집계 지표 선택", ["화재 발생 건수 (건)", "인명피해 합계 (명)", "재산피해 합계 (천원)"], key="t3_metric_select")

    is_damage_heat = "재산피해" in heat_metric
    if is_damage_heat:
        use_log_heat = st.toggle(
            " 피해금액 로그 정규화 (Log Scale) 색상 적용 (권장)",
            value=True,
            help="산업시설 등 특정 분야의 압도적인 피해금액으로 인한 색상 쏠림을 보정하여 전 분야의 피해 규모를 고르게 시각화합니다."
        )
    else:
        use_log_heat = False

    heat_data = df.copy()
    if "소분류" in cause_level:
        top_causes = heat_data["발화요인소분류"].value_counts().nlargest(15).index
        heat_data = heat_data[heat_data["발화요인소분류"].isin(top_causes)]
        cause_col_name = "발화요인소분류"
    else:
        cause_col_name = "발화요인대분류"

    if "화재 발생 건수" in heat_metric:
        pvt = pd.crosstab(heat_data[cause_col_name], heat_data["장소대분류"])
        u_str = "건"
        c_scale = "YlOrRd"
    elif "인명피해" in heat_metric:
        pvt = heat_data.pivot_table(index=cause_col_name, columns="장소대분류", values="인명피해(명)소계", aggfunc="sum", fill_value=0)
        u_str = "명"
        c_scale = "OrRd"
    else:
        pvt = heat_data.pivot_table(index=cause_col_name, columns="장소대분류", values="재산피해소계", aggfunc="sum", fill_value=0)
        u_str = "천원"
        c_scale = "Reds"

    row_sort = pvt.sum(axis=1).sort_values(ascending=True).index
    col_sort = pvt.sum(axis=0).sort_values(ascending=False).index
    pvt = pvt.reindex(index=row_sort, columns=col_sort)

    # 색상 스케일 매핑용 z_color 계산 (재산피해이고 로그정규화 적용 시 log10 적용)
    if is_damage_heat and use_log_heat:
        z_color = np.log10(pvt.values + 1)
        # 로그 스케일에서 0이 아닌 값들 중 상위 75% 백분위수를 임계값으로 적용
        positive_logs = z_color[z_color > 0]
        threshold_color = np.percentile(positive_logs, 75) if len(positive_logs) > 0 else 1.0
    else:
        z_color = pvt.values
        max_val = float(pvt.values.max()) if pvt.values.max() > 0 else 1.0
        threshold_color = max_val * 0.5

    annotations = []
    for r_idx, r_name in enumerate(pvt.index):
        for c_idx, c_name in enumerate(pvt.columns):
            val = pvt.loc[r_name, c_name]
            c_val = z_color[r_idx, c_idx]
            text_color = "#ffffff" if c_val >= threshold_color else "#000000"
            
            # 재산피해일 때는 알아보기 쉬운 한국어 금액 단위(억/천만/만)로 표시
            if is_damage_heat:
                disp_text = format_korean_money(val)
            else:
                disp_text = f"{val:,}"

            annotations.append(dict(
                x=c_name,
                y=r_name,
                text=disp_text,
                showarrow=False,
                font=dict(size=10.5, color=text_color, family="sans-serif")
            ))

    custom_tooltips = []
    for r in pvt.index:
        row_tips = []
        for c in pvt.columns:
            raw_v = pvt.loc[r, c]
            if is_damage_heat:
                row_tips.append(f"{format_korean_money(raw_v)}원 ({raw_v:,}천원)")
            else:
                row_tips.append(f"{raw_v:,}{u_str}")
        custom_tooltips.append(row_tips)

    fig_heat_main = go.Figure(data=go.Heatmap(
        z=z_color,
        x=pvt.columns.tolist(),
        y=pvt.index.tolist(),
        colorscale=c_scale,
        hoverongaps=False,
        customdata=custom_tooltips,
        hovertemplate="<b>장소:</b> %{x}<br><b>발화요인:</b> %{y}<br><b>피해 수치:</b> %{customdata}<extra></extra>",
        colorbar=dict(
            title=dict(text="로그 스케일" if (is_damage_heat and use_log_heat) else u_str)
        )
    ))
    apply_chart_theme(fig_heat_main, f"[{cause_col_name} × 장소대분류] {heat_metric} 매트릭스", height=600)
    fig_heat_main.update_layout(
        annotations=annotations,
        xaxis=dict(tickangle=-30, title="<b>장소 대분류</b>"),
        yaxis=dict(autorange="reversed", title=f"<b>{cause_col_name}</b>")
    )
    st.plotly_chart(fig_heat_main, width="stretch")

    top_pair = pvt.stack().idxmax()
    top_pair_val = pvt.stack().max()
    st.info(f" **발화요인 인사이트:** 가장 높은 수치를 기록한 조합은 **[{top_pair[0]} × {top_pair[1]}]** (총 **{top_pair_val:,} {u_str}**) 입니다.")
