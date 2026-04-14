import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Streamlit BI x Claude Code Starter", layout="wide")

st.title("Streamlit BI x Claude Code Starter")


@st.cache_data
def load_data():
    orders_df = pd.read_csv("sample_data/orders.csv", parse_dates=["created_at"])
    users_df = pd.read_csv("sample_data/users.csv", parse_dates=["created_at"])
    return orders_df, users_df


orders_df, users_df = load_data()

# ── 파생 컬럼 ──────────────────────────────────────────────
orders_df["year_month"] = orders_df["created_at"].dt.to_period("M").astype(str)
users_df["age_group"] = pd.cut(
    users_df["age"],
    bins=[0, 19, 29, 39, 49, 59, 100],
    labels=["10대", "20대", "30대", "40대", "50대", "60대+"],
)

total_orders = len(orders_df)
total_users = len(users_df)
complete_rate = orders_df["status"].eq("Complete").mean() * 100
cancel_rate = orders_df["status"].eq("Cancelled").mean() * 100

# ── 1. KPI 카드 ────────────────────────────────────────────
st.subheader("핵심 지표")
k1, k2, k3, k4 = st.columns(4)
k1.metric("총 주문 수", f"{total_orders:,}")
k2.metric("총 유저 수", f"{total_users:,}")
k3.metric("주문 완료율", f"{complete_rate:.1f}%")
k4.metric("주문 취소율", f"{cancel_rate:.1f}%")

st.divider()

# ── 2. 주문 현황 ────────────────────────────────────────────
st.subheader("주문 현황")
col_left, col_right = st.columns(2)

with col_left:
    status_counts = orders_df["status"].value_counts().reset_index()
    status_counts.columns = ["status", "count"]
    fig_pie = px.pie(
        status_counts,
        names="status",
        values="count",
        title="주문 상태 분포",
        hole=0.4,
    )
    fig_pie.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig_pie, use_container_width=True)

with col_right:
    monthly = orders_df.groupby("year_month").size().reset_index(name="count")
    fig_line = px.line(
        monthly,
        x="year_month",
        y="count",
        title="월별 주문 추이",
        markers=True,
        labels={"year_month": "월", "count": "주문 수"},
    )
    fig_line.update_xaxes(tickangle=-45)
    st.plotly_chart(fig_line, use_container_width=True)

st.divider()

# ── 3. 유저 분석 ────────────────────────────────────────────
st.subheader("유저 분석")
u1, u2, u3 = st.columns(3)

with u1:
    top_countries = users_df["country"].value_counts().head(5).reset_index()
    top_countries.columns = ["country", "count"]
    fig_country = px.bar(
        top_countries,
        x="count",
        y="country",
        orientation="h",
        title="국가별 유저 Top 5",
        labels={"count": "유저 수", "country": "국가"},
    )
    fig_country.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_country, use_container_width=True)

with u2:
    age_counts = users_df["age_group"].value_counts().sort_index().reset_index()
    age_counts.columns = ["age_group", "count"]
    fig_age = px.bar(
        age_counts,
        x="age_group",
        y="count",
        title="연령대별 유저 분포",
        labels={"age_group": "연령대", "count": "유저 수"},
        color="age_group",
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig_age.update_layout(showlegend=False)
    st.plotly_chart(fig_age, use_container_width=True)

with u3:
    src_counts = users_df["traffic_source"].value_counts().reset_index()
    src_counts.columns = ["source", "count"]
    fig_src = px.pie(
        src_counts,
        names="source",
        values="count",
        title="유입 채널 분포",
        hole=0.35,
    )
    st.plotly_chart(fig_src, use_container_width=True)

st.divider()

# ── 4. 교차 분석 ────────────────────────────────────────────
st.subheader("교차 분석")
c1, c2 = st.columns(2)

with c1:
    gender_status = (
        orders_df.groupby(["gender", "status"])
        .size()
        .reset_index(name="count")
    )
    fig_gs = px.bar(
        gender_status,
        x="status",
        y="count",
        color="gender",
        barmode="group",
        title="성별 × 주문 상태",
        labels={"count": "주문 수", "status": "상태", "gender": "성별"},
    )
    st.plotly_chart(fig_gs, use_container_width=True)

with c2:
    merged = orders_df.merge(
        users_df[["id", "traffic_source"]], left_on="user_id", right_on="id", how="left"
    )
    channel_rate = (
        merged.groupby("traffic_source")["status"]
        .apply(lambda x: (x == "Complete").mean() * 100)
        .reset_index(name="완료율(%)")
    )
    fig_cr = px.bar(
        channel_rate,
        x="traffic_source",
        y="완료율(%)",
        title="유입 채널별 주문 완료율",
        labels={"traffic_source": "채널"},
        color="완료율(%)",
        color_continuous_scale="Blues",
    )
    st.plotly_chart(fig_cr, use_container_width=True)

st.divider()

# ── 5. 월별 트렌드 ─────────────────────────────────────────
st.subheader("월별 트렌드")
t1, t2 = st.columns(2)

with t1:
    monthly_bar = orders_df.groupby("year_month").size().reset_index(name="주문 수")
    fig_bar = px.bar(
        monthly_bar,
        x="year_month",
        y="주문 수",
        title="월별 주문 수",
        labels={"year_month": "월"},
        color="주문 수",
        color_continuous_scale="Blues",
    )
    fig_bar.update_xaxes(tickangle=-45)
    fig_bar.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig_bar, use_container_width=True)

with t2:
    monthly_cancel = (
        orders_df.groupby("year_month")["status"]
        .apply(lambda x: (x == "Cancelled").mean() * 100)
        .reset_index(name="취소율(%)")
    )
    fig_cancel = px.line(
        monthly_cancel,
        x="year_month",
        y="취소율(%)",
        title="월별 취소율",
        markers=True,
        labels={"year_month": "월"},
    )
    fig_cancel.update_xaxes(tickangle=-45)
    fig_cancel.update_traces(line_color="#EF553B", marker_color="#EF553B")
    st.plotly_chart(fig_cancel, use_container_width=True)

st.divider()

# ── 6. 원본 데이터 (확장 패널) ─────────────────────────────
with st.expander("원본 데이터 보기"):
    st.subheader("Orders (상위 10행)")
    st.dataframe(orders_df.head(10))
    st.subheader("Users (상위 10행)")
    st.dataframe(users_df.head(10))
