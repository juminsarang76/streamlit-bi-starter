import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="나쁜 판매 상품 분석", layout="wide")

st.title("나쁜 판매 상품 분석")
st.caption("반품율·취소율·판매량·추세를 기반으로 문제 상품을 탐지합니다.")


@st.cache_data
def load_data():
    items = pd.read_csv("sample_data/order_items.csv", parse_dates=["created_at"])
    products = pd.read_csv("sample_data/products.csv")

    df = items.merge(
        products[["id", "name", "category", "brand", "department", "cost", "retail_price"]],
        left_on="product_id",
        right_on="id",
        how="left",
    )
    df["year_month"] = df["created_at"].dt.to_period("M").astype(str)

    # 상품별 집계
    prod = (
        df.groupby(["product_id", "name", "category", "brand", "department", "cost", "retail_price"])
        .agg(
            판매건수=("sale_price", "count"),
            총매출=("sale_price", "sum"),
            평균판매가=("sale_price", "mean"),
            반품건수=("status", lambda x: (x == "Returned").sum()),
            취소건수=("status", lambda x: (x == "Cancelled").sum()),
        )
        .reset_index()
    )

    prod["반품율"] = prod["반품건수"] / prod["판매건수"] * 100
    prod["취소율"] = prod["취소건수"] / prod["판매건수"] * 100
    prod["마진율"] = (prod["평균판매가"] - prod["cost"]) / prod["평균판매가"] * 100

    # 복합 위험 점수 (반품율 40% + 취소율 30% + 저판매 가중치 30%)
    max_sales = prod["판매건수"].max()
    prod["위험점수"] = (
        (prod["반품율"] / 100) * 40
        + (prod["취소율"] / 100) * 30
        + (1 - prod["판매건수"] / max_sales) * 30
    ).round(2)

    return df, prod, products


df, prod, products = load_data()

# ── 사이드바 ────────────────────────────────────────────────
st.sidebar.header("필터")
min_sales = st.sidebar.slider("최소 판매건수 (반품율 분석 기준)", 1, 10, 5)
dept_filter = st.sidebar.radio("부서", ["전체", "Women", "Men"], horizontal=True)

prod_f = prod.copy()
if dept_filter != "전체":
    prod_f = prod_f[prod_f["department"] == dept_filter]

df_f = df.copy()
if dept_filter != "전체":
    df_f = df_f[df_f["department"] == dept_filter]

# ── 1. KPI 카드 ────────────────────────────────────────────
st.subheader("핵심 지표")
k1, k2, k3, k4 = st.columns(4)

high_return = prod_f[prod_f["판매건수"] >= min_sales].query("반품율 >= 40")
dead_stock   = prod_f[prod_f["판매건수"] == 1]
high_risk    = prod_f[prod_f["위험점수"] >= 50]
avg_return   = prod_f["반품율"].mean()

k1.metric("고반품율 상품 (≥40%)", f"{len(high_return):,}개")
k2.metric("Dead Stock (판매 1건)", f"{len(dead_stock):,}개")
k3.metric("고위험 상품 (점수≥50)", f"{len(high_risk):,}개")
k4.metric("전체 평균 반품율", f"{avg_return:.1f}%")

st.divider()

# ── 2. 고반품율 상품 ────────────────────────────────────────
st.subheader(f"고반품율 상품 Top 20  (판매 {min_sales}건 이상, 반품율 ≥ 40%)")

high_return_top = (
    prod_f[prod_f["판매건수"] >= min_sales]
    .sort_values("반품율", ascending=False)
    .head(20)
)

col1, col2 = st.columns([3, 2])

with col1:
    if high_return_top.empty:
        st.info("해당 조건의 상품이 없습니다.")
    else:
        fig_hr = px.bar(
            high_return_top.sort_values("반품율"),
            x="반품율",
            y="name",
            orientation="h",
            color="반품율",
            color_continuous_scale="Reds",
            title="상품별 반품율 (%)",
            labels={"name": "상품명", "반품율": "반품율 (%)"},
            hover_data=["category", "brand", "판매건수", "취소율"],
        )
        fig_hr.update_layout(coloraxis_showscale=False, yaxis_title="", height=550)
        st.plotly_chart(fig_hr, use_container_width=True)

with col2:
    st.dataframe(
        high_return_top[["name", "category", "판매건수", "반품율", "취소율", "마진율"]]
        .rename(columns={"name": "상품명", "category": "카테고리"})
        .round(1)
        .reset_index(drop=True),
        height=550,
    )

st.divider()

# ── 3. Dead Stock ───────────────────────────────────────────
st.subheader("Dead Stock — 판매 1건 상품")

dead_by_cat = (
    dead_stock.groupby("category")
    .size()
    .reset_index(name="Dead Stock 수")
    .sort_values("Dead Stock 수", ascending=False)
)

total_by_cat = (
    prod_f.groupby("category")
    .size()
    .reset_index(name="전체 수")
)

dead_ratio = dead_by_cat.merge(total_by_cat, on="category")
dead_ratio["비율(%)"] = (dead_ratio["Dead Stock 수"] / dead_ratio["전체 수"] * 100).round(1)

col3, col4 = st.columns(2)

with col3:
    fig_dead = px.bar(
        dead_ratio.sort_values("Dead Stock 수", ascending=True),
        x="Dead Stock 수",
        y="category",
        orientation="h",
        title="카테고리별 Dead Stock 수",
        color="Dead Stock 수",
        color_continuous_scale="Oranges",
        labels={"category": "카테고리"},
    )
    fig_dead.update_layout(coloraxis_showscale=False, yaxis_title="")
    st.plotly_chart(fig_dead, use_container_width=True)

with col4:
    fig_ratio = px.bar(
        dead_ratio.sort_values("비율(%)", ascending=True),
        x="비율(%)",
        y="category",
        orientation="h",
        title="카테고리별 Dead Stock 비율",
        color="비율(%)",
        color_continuous_scale="YlOrRd",
        labels={"category": "카테고리"},
    )
    fig_ratio.update_layout(coloraxis_showscale=False, yaxis_title="")
    st.plotly_chart(fig_ratio, use_container_width=True)

st.divider()

# ── 4. 복합 위험 점수 Top 20 ───────────────────────────────
st.subheader("복합 위험 점수 Top 20")
st.caption("위험점수 = 반품율×40% + 취소율×30% + 저판매 가중치×30%")

risk_top = prod_f.sort_values("위험점수", ascending=False).head(20)

col5, col6 = st.columns([3, 2])

with col5:
    fig_risk = px.bar(
        risk_top.sort_values("위험점수"),
        x="위험점수",
        y="name",
        orientation="h",
        color="위험점수",
        color_continuous_scale="RdYlGn_r",
        title="복합 위험 점수 상위 20개 상품",
        labels={"name": "상품명"},
        hover_data=["category", "반품율", "취소율", "판매건수"],
    )
    fig_risk.update_layout(coloraxis_showscale=False, yaxis_title="", height=550)
    st.plotly_chart(fig_risk, use_container_width=True)

with col6:
    st.dataframe(
        risk_top[["name", "category", "판매건수", "반품율", "취소율", "위험점수"]]
        .rename(columns={"name": "상품명", "category": "카테고리"})
        .round(1)
        .reset_index(drop=True),
        height=550,
    )

st.divider()

# ── 5. 판매 하락 추세 상품 ─────────────────────────────────
st.subheader("판매 하락 추세 상품")
st.caption("초반 3개월(2025-01~03) 대비 최근 3개월(2025-05~07) 판매량이 50% 이상 감소한 상품")

monthly_prod = (
    df_f.groupby(["year_month", "product_id", "name", "category"])
    .size()
    .reset_index(name="건수")
)

early = monthly_prod[monthly_prod["year_month"].isin(["2025-01", "2025-02", "2025-03"])]
recent = monthly_prod[monthly_prod["year_month"].isin(["2025-05", "2025-06", "2025-07"])]

early_sum  = early.groupby(["product_id", "name", "category"])["건수"].sum().reset_index(name="초반_건수")
recent_sum = recent.groupby(["product_id", "name", "category"])["건수"].sum().reset_index(name="최근_건수")

trend = early_sum.merge(recent_sum, on=["product_id", "name", "category"])
trend["감소율(%)"] = ((trend["초반_건수"] - trend["최근_건수"]) / trend["초반_건수"] * 100).round(1)
decline = trend[trend["감소율(%)"] >= 50].sort_values("감소율(%)", ascending=False)

col7, col8 = st.columns([3, 2])

with col7:
    if decline.empty:
        st.info("50% 이상 하락한 상품이 없습니다.")
    else:
        # 하락 상위 5개 상품의 월별 추이
        top5_decline = decline.head(5)["product_id"].tolist()
        top5_monthly = monthly_prod[monthly_prod["product_id"].isin(top5_decline)]

        fig_decline = px.line(
            top5_monthly,
            x="year_month",
            y="건수",
            color="name",
            markers=True,
            title="하락 추세 Top 5 상품 월별 판매량",
            labels={"year_month": "월", "건수": "판매 건수", "name": "상품명"},
        )
        fig_decline.update_xaxes(tickangle=-45)
        st.plotly_chart(fig_decline, use_container_width=True)

with col8:
    st.dataframe(
        decline[["name", "category", "초반_건수", "최근_건수", "감소율(%)"]].head(20)
        .rename(columns={"name": "상품명", "category": "카테고리",
                          "초반_건수": "초반(1~3월)", "최근_건수": "최근(5~7월)"})
        .reset_index(drop=True),
        height=400,
    )

st.divider()

# ── 6. 고가격 & 저판매 산점도 ─────────────────────────────
st.subheader("가격 vs 판매량 포지셔닝 (사분면 분석)")
st.caption("우상단: 고가·고판매(우량) | 우하단: 고가·저판매(문제) | 좌하단: 저가·저판매(철수 검토)")

price_med  = prod_f["retail_price"].median()
sales_med  = prod_f["판매건수"].median()

def quadrant(row):
    high_p = row["retail_price"] >= price_med
    high_s = row["판매건수"] >= sales_med
    if high_p and high_s:
        return "고가·고판매 (우량)"
    elif high_p and not high_s:
        return "고가·저판매 (문제)"
    elif not high_p and high_s:
        return "저가·고판매 (대중)"
    else:
        return "저가·저판매 (철수 검토)"

prod_f = prod_f.copy()
prod_f["사분면"] = prod_f.apply(quadrant, axis=1)

color_map = {
    "고가·고판매 (우량)":    "#00CC96",
    "고가·저판매 (문제)":    "#EF553B",
    "저가·고판매 (대중)":    "#636EFA",
    "저가·저판매 (철수 검토)": "#FFA15A",
}

fig_quad = px.scatter(
    prod_f,
    x="retail_price",
    y="판매건수",
    color="사분면",
    color_discrete_map=color_map,
    opacity=0.6,
    title="가격 × 판매량 사분면",
    labels={"retail_price": "정가 ($)", "판매건수": "판매 건수"},
    hover_data=["name", "category", "brand", "반품율"],
)
fig_quad.add_vline(x=price_med, line_dash="dash", line_color="gray", annotation_text=f"중앙값 ${price_med:.0f}")
fig_quad.add_hline(y=sales_med, line_dash="dash", line_color="gray", annotation_text=f"중앙값 {sales_med:.0f}건")
fig_quad.update_layout(height=500)
st.plotly_chart(fig_quad, use_container_width=True)

# 사분면별 요약
quad_summary = (
    prod_f.groupby("사분면")
    .agg(상품수=("product_id", "count"), 평균반품율=("반품율", "mean"))
    .round(1)
    .reset_index()
)
st.dataframe(quad_summary, use_container_width=True, hide_index=True)

st.divider()

# ── 7. 원본 데이터 ─────────────────────────────────────────
with st.expander("상품별 전체 집계 데이터"):
    st.dataframe(
        prod_f[["name", "category", "brand", "department",
                "판매건수", "반품율", "취소율", "마진율", "위험점수", "총매출"]]
        .rename(columns={"name": "상품명", "category": "카테고리",
                          "brand": "브랜드", "department": "부서"})
        .sort_values("위험점수", ascending=False)
        .round(1)
        .reset_index(drop=True),
        use_container_width=True,
    )
