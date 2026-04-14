import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

st.set_page_config(page_title="카테고리 판매 분석", layout="wide")

st.title("제품 카테고리 판매 분석")


@st.cache_data
def load_data():
    items = pd.read_csv("sample_data/order_items.csv", parse_dates=["created_at"])
    products = pd.read_csv("sample_data/products.csv")
    df = items.merge(
        products[["id", "category", "brand", "department", "retail_price", "cost"]],
        left_on="product_id",
        right_on="id",
        how="left",
    )
    df["margin"] = (df["sale_price"] - df["cost"]) / df["sale_price"] * 100
    df["year_month"] = df["created_at"].dt.to_period("M").astype(str)
    return df, products


df, products = load_data()

# ── 사이드바 필터 ───────────────────────────────────────────
st.sidebar.header("필터")

# 날짜 범위 선택
date_min = df["created_at"].min().date()
date_max = df["created_at"].max().date()
selected_dates = st.sidebar.date_input(
    "분석 기간",
    value=(date_min, date_max),
    min_value=date_min,
    max_value=date_max,
    format="YYYY-MM-DD",
)

# 두 날짜가 모두 선택된 경우에만 필터 적용
if isinstance(selected_dates, (list, tuple)) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
else:
    start_date, end_date = date_min, date_max

st.sidebar.caption(f"선택 기간: {start_date} ~ {end_date}")

dept_options = ["전체"] + sorted(df["department"].dropna().unique().tolist())
selected_dept = st.sidebar.radio("성별 (부서)", dept_options, horizontal=True)
selected_status = st.sidebar.multiselect(
    "주문 상태",
    options=df["status"].unique().tolist(),
    default=df["status"].unique().tolist(),
)

filtered = df[
    (df["created_at"].dt.date >= start_date) &
    (df["created_at"].dt.date <= end_date)
].copy()
if selected_dept != "전체":
    filtered = filtered[filtered["department"] == selected_dept]
if selected_status:
    filtered = filtered[filtered["status"].isin(selected_status)]

# ── 1. KPI 카드 ────────────────────────────────────────────
st.subheader("핵심 지표")
k1, k2, k3, k4 = st.columns(4)
total_revenue = filtered["sale_price"].sum()
num_categories = filtered["category"].nunique()
avg_price = filtered["sale_price"].mean()
return_rate = filtered["status"].eq("Returned").mean() * 100

k1.metric("총 매출", f"${total_revenue:,.0f}")
k2.metric("카테고리 수", f"{num_categories}")
k3.metric("평균 판매가", f"${avg_price:.2f}")
k4.metric("반품률", f"{return_rate:.1f}%")

st.divider()

# ── 2. 카테고리별 매출 & 마진 ──────────────────────────────
st.subheader("카테고리별 매출 & 마진")
col1, col2 = st.columns(2)

with col1:
    cat_revenue = (
        filtered.groupby("category")["sale_price"]
        .sum()
        .reset_index(name="매출")
        .sort_values("매출", ascending=True)
        .tail(15)
    )
    fig_rev = px.bar(
        cat_revenue,
        x="매출",
        y="category",
        orientation="h",
        title="카테고리별 총 매출 Top 15",
        labels={"category": "카테고리", "매출": "매출 ($)"},
        color="매출",
        color_continuous_scale="Blues",
    )
    fig_rev.update_layout(coloraxis_showscale=False, yaxis_title="")
    st.plotly_chart(fig_rev, use_container_width=True)

with col2:
    cat_margin = (
        filtered.groupby("category")["margin"]
        .mean()
        .reset_index(name="평균 마진율(%)")
        .sort_values("평균 마진율(%)", ascending=True)
        .tail(15)
    )
    fig_margin = px.bar(
        cat_margin,
        x="평균 마진율(%)",
        y="category",
        orientation="h",
        title="카테고리별 평균 마진율 Top 15",
        labels={"category": "카테고리"},
        color="평균 마진율(%)",
        color_continuous_scale="Greens",
    )
    fig_margin.update_layout(coloraxis_showscale=False, yaxis_title="")
    st.plotly_chart(fig_margin, use_container_width=True)

st.divider()

# ── 3. 볼륨 vs 단가 버블 차트 ─────────────────────────────
st.subheader("카테고리 포지셔닝 (판매량 vs 평균 단가)")
bubble = filtered.groupby("category").agg(
    판매량=("sale_price", "count"),
    평균단가=("sale_price", "mean"),
    총매출=("sale_price", "sum"),
).reset_index()

fig_bubble = px.scatter(
    bubble,
    x="판매량",
    y="평균단가",
    size="총매출",
    color="category",
    title="카테고리별 판매량 × 평균 단가 (버블 크기 = 총 매출)",
    labels={"판매량": "판매 건수", "평균단가": "평균 판매가 ($)", "category": "카테고리"},
    hover_name="category",
    size_max=60,
)
fig_bubble.update_layout(showlegend=False)
st.plotly_chart(fig_bubble, use_container_width=True)

st.divider()

# ── 4. 부서별 매출 비교 & 카테고리별 반품·취소율 ──────────
st.subheader("부서별 비교 & 카테고리별 이슈율")
col3, col4 = st.columns(2)

with col3:
    dept_rev = (
        filtered.groupby("department")["sale_price"]
        .sum()
        .reset_index(name="매출")
    )
    fig_dept = px.pie(
        dept_rev,
        names="department",
        values="매출",
        title="부서별 매출 비중 (Women / Men)",
        hole=0.4,
        color_discrete_sequence=["#636EFA", "#EF553B"],
    )
    st.plotly_chart(fig_dept, use_container_width=True)

with col4:
    issue = (
        filtered.groupby("category")
        .apply(
            lambda x: pd.Series({
                "취소율(%)": (x["status"] == "Cancelled").mean() * 100,
                "반품율(%)": (x["status"] == "Returned").mean() * 100,
            }),
            include_groups=False,
        )
        .reset_index()
    )
    issue_top = issue.sort_values("반품율(%)", ascending=False).head(12)
    fig_issue = px.bar(
        issue_top.melt(id_vars="category", var_name="구분", value_name="비율(%)"),
        x="category",
        y="비율(%)",
        color="구분",
        barmode="group",
        title="카테고리별 취소율·반품율 Top 12",
        labels={"category": "카테고리"},
        color_discrete_map={"취소율(%)": "#FFA15A", "반품율(%)": "#EF553B"},
    )
    fig_issue.update_xaxes(tickangle=-45)
    st.plotly_chart(fig_issue, use_container_width=True)

st.divider()

# ── 5. 브랜드 Top 10 매출 ──────────────────────────────────
st.subheader("브랜드 Top 10 매출")
brand_rev = (
    filtered.groupby("brand")["sale_price"]
    .sum()
    .reset_index(name="매출")
    .sort_values("매출", ascending=False)
    .head(10)
)
fig_brand = px.bar(
    brand_rev,
    x="brand",
    y="매출",
    title="브랜드별 총 매출 Top 10",
    labels={"brand": "브랜드", "매출": "매출 ($)"},
    color="매출",
    color_continuous_scale="Purples",
)
fig_brand.update_layout(coloraxis_showscale=False)
st.plotly_chart(fig_brand, use_container_width=True)

st.divider()

# ── 6. 월별 카테고리 매출 추이 ─────────────────────────────
st.subheader("월별 카테고리 매출 추이")
top5_cats = (
    filtered.groupby("category")["sale_price"]
    .sum()
    .nlargest(5)
    .index.tolist()
)
monthly_cat = (
    filtered[filtered["category"].isin(top5_cats)]
    .groupby(["year_month", "category"])["sale_price"]
    .sum()
    .reset_index(name="매출")
)
fig_trend = px.line(
    monthly_cat,
    x="year_month",
    y="매출",
    color="category",
    title="매출 Top 5 카테고리 월별 추이",
    markers=True,
    labels={"year_month": "월", "매출": "매출 ($)", "category": "카테고리"},
)
fig_trend.update_xaxes(tickangle=-45)
st.plotly_chart(fig_trend, use_container_width=True)

st.divider()

# ── 7. 원본 데이터 ─────────────────────────────────────────
with st.expander("원본 데이터 보기"):
    st.dataframe(
        filtered[["category", "brand", "department", "sale_price", "cost", "margin", "status", "year_month"]]
        .sort_values("sale_price", ascending=False)
        .head(100)
        .reset_index(drop=True)
    )
