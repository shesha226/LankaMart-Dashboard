import pandas as pd
import streamlit as st
import plotly.express as px



st.set_page_config(
    page_title="LankaMart Executive Dashboard",
    layout="wide"
)




@st.cache_data
def load_data():

    df = pd.read_csv(
        "CIT308_LankaMart_Retail_Transactions.csv"
    )

    df["order_date"] = pd.to_datetime(
        df["order_date"],
        errors="coerce"
    )

    if "product_category" in df.columns:
        df["product_category"] = (
            df["product_category"]
            .astype(str)
            .str.strip()
            .str.title()
        )

    text_columns = [
        "province",
        "city",
        "sales_channel",
        "customer_segment",
        "product_name",
        "payment_method",
        "returned",
        "promotion"
    ]

    for column in text_columns:
        if column in df.columns:
            df[column] = (
                df[column]
                .astype("string")
                .str.strip()
            )

   

    df = df.drop_duplicates()

  

    if "customer_rating" in df.columns:

        median_rating = df["customer_rating"].median()

        df["customer_rating"] = (
            df["customer_rating"]
            .fillna(median_rating)
        )

 

    df["month"] = (
        df["order_date"]
        .dt.to_period("M")
        .dt.to_timestamp()
    )

   

    df["profit_margin"] = 0.0

    valid_revenue = df["revenue_lkr"] > 0

    df.loc[valid_revenue, "profit_margin"] = (
        df.loc[valid_revenue, "profit_lkr"]
        / df.loc[valid_revenue, "revenue_lkr"]
        * 100
    )

   

    def delivery_band(days):

        if pd.isna(days):
            return "Unknown"

        if days <= 2:
            return "Fast"

        elif days <= 5:
            return "Standard"

        else:
            return "Slow"

    df["delivery_performance"] = (
        df["delivery_days"]
        .apply(delivery_band)
    )

    return df


df = load_data()




st.title(
    "🛒 LankaMart - Executive Performance Dashboard"
)

st.caption(
    "Interactive analysis of sales performance, profitability, "
    "customer behaviour, fulfilment quality and product returns."
)




with st.expander("🔍 Data Quality & Preparation Checks"):

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Rows",
            f"{len(df):,}"
        )

    with col2:
        st.metric(
            "Columns",
            f"{len(df.columns):,}"
        )

    with col3:
        st.metric(
            "Missing Values",
            f"{df.isnull().sum().sum():,}"
        )

    with col4:
        st.metric(
            "Duplicate Rows",
            f"{df.duplicated().sum():,}"
        )

    st.write("### Data Types")

    dtype_df = pd.DataFrame({
        "Column": df.columns,
        "Data Type": df.dtypes.astype(str)
    })

    st.dataframe(
        dtype_df,
        use_container_width=True,
        hide_index=True
    )

    st.write("### Missing Values")

    missing_df = pd.DataFrame({
        "Column": df.columns,
        "Missing Values": df.isnull().sum().values
    })

    missing_df["Missing Percentage"] = (
        missing_df["Missing Values"]
        / len(df)
        * 100
    ).round(2)

    st.dataframe(
        missing_df,
        use_container_width=True,
        hide_index=True
    )

    st.write(
        "### Calculated Fields"
    )

    st.markdown(
        """
        - **Month** – extracted from `order_date` for monthly trend analysis.
        - **Profit Margin** – calculated as profit divided by revenue × 100.
        - **Delivery Performance** – orders are classified as Fast (≤2 days),
          Standard (3–5 days) or Slow (>5 days).
        - Missing customer ratings are replaced using the median rating.
        - Complete duplicate rows are removed.
        """
    )




st.sidebar.header("🎛️ Dashboard Filters")

st.sidebar.markdown(
    "Use the filters below to analyse different parts of the business."
)




min_date = df["order_date"].min().date()
max_date = df["order_date"].max().date()

date_range = st.sidebar.date_input(
    "📅 Order Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)




province_options = sorted(
    df["province"]
    .dropna()
    .unique()
    .tolist()
)

selected_province = st.sidebar.selectbox(
    " Province",
    ["All"] + province_options
)



channel_options = sorted(
    df["sales_channel"]
    .dropna()
    .unique()
    .tolist()
)

selected_channel = st.sidebar.selectbox(
    " Sales Channel",
    ["All"] + channel_options
)




category_options = sorted(
    df["product_category"]
    .dropna()
    .unique()
    .tolist()
)

selected_category = st.sidebar.selectbox(
    " Product Category",
    ["All"] + category_options
)




if st.sidebar.button(
    " Reset Filters",
    use_container_width=True
):

    st.session_state.clear()
    st.rerun()


filtered_df = df.copy()


if len(date_range) == 2:

    start_date = pd.Timestamp(date_range[0])

    end_date = (
        pd.Timestamp(date_range[1])
        + pd.Timedelta(days=1)
    )

    filtered_df = filtered_df[
        (filtered_df["order_date"] >= start_date)
        &
        (filtered_df["order_date"] < end_date)
    ]


if selected_province != "All":

    filtered_df = filtered_df[
        filtered_df["province"]
        == selected_province
    ]


if selected_channel != "All":

    filtered_df = filtered_df[
        filtered_df["sales_channel"]
        == selected_channel
    ]


if selected_category != "All":

    filtered_df = filtered_df[
        filtered_df["product_category"]
        == selected_category
    ]



st.info(
    f"Showing **{len(filtered_df):,}** records "
    f"from **{len(df):,}** total records."
)




total_revenue = filtered_df["revenue_lkr"].sum()

total_profit = filtered_df["profit_lkr"].sum()

profit_margin = (
    total_profit
    / total_revenue
    * 100
    if total_revenue > 0
    else 0
)

return_count = (
    filtered_df["returned"]
    .eq("Yes")
    .sum()
)

return_rate = (
    return_count
    / len(filtered_df)
    * 100
    if len(filtered_df) > 0
    else 0
)




st.subheader("📊 Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "💰 Total Revenue",
        f"LKR {total_revenue:,.2f}"
    )

with col2:

    st.metric(
        "📈 Total Profit",
        f"LKR {total_profit:,.2f}"
    )

with col3:

    st.metric(
        "📊 Profit Margin",
        f"{profit_margin:.2f}%"
    )

with col4:

    st.metric(
        "↩️ Return Rate",
        f"{return_rate:.2f}%"
    )


st.markdown("---")




st.subheader("📈 Monthly Revenue and Profit Trend")

if not filtered_df.empty:

    trend_df = (
        filtered_df
        .groupby("month", as_index=False)
        .agg(
            Revenue=("revenue_lkr", "sum"),
            Profit=("profit_lkr", "sum")
        )
    )

    trend_long = trend_df.melt(
        id_vars="month",
        value_vars=["Revenue", "Profit"],
        var_name="Metric",
        value_name="LKR"
    )

    fig_trend = px.line(
        trend_long,
        x="month",
        y="LKR",
        color="Metric",
        markers=True,
        title="Monthly Revenue and Profit Trend",
        labels={
            "month": "Month",
            "LKR": "Amount (LKR)",
            "Metric": "Measure"
        }
    )

    fig_trend.update_layout(
        hovermode="x unified"
    )

    st.plotly_chart(
        fig_trend,
        use_container_width=True
    )

else:

    st.warning("No data available for the selected filters.")



row2_col1, row2_col2 = st.columns(2)


with row2_col1:

    category_df = (
        filtered_df
        .groupby("product_category", as_index=False)
        .agg(
            Revenue=("revenue_lkr", "sum"),
            Profit=("profit_lkr", "sum")
        )
        .sort_values(
            "Revenue",
            ascending=False
        )
    )

    fig_category = px.bar(
        category_df,
        x="product_category",
        y="Revenue",
        title="Revenue by Product Category",
        labels={
            "product_category": "Product Category",
            "Revenue": "Revenue (LKR)"
        },
        text_auto=".2s"
    )

    st.plotly_chart(
        fig_category,
        use_container_width=True
    )




with row2_col2:

    province_df = (
        filtered_df
        .groupby("province", as_index=False)
        .agg(
            Revenue=("revenue_lkr", "sum"),
            Profit=("profit_lkr", "sum")
        )
        .sort_values(
            "Revenue",
            ascending=False
        )
    )

    fig_province = px.bar(
        province_df,
        x="province",
        y="Revenue",
        title="Revenue Performance by Province",
        labels={
            "province": "Province",
            "Revenue": "Revenue (LKR)"
        },
        text_auto=".2s"
    )

    st.plotly_chart(
        fig_province,
        use_container_width=True
    )


row3_col1, row3_col2 = st.columns(2)


with row3_col1:

    channel_df = (
        filtered_df
        .groupby("sales_channel", as_index=False)
        .agg(
            Revenue=("revenue_lkr", "sum"),
            Profit=("profit_lkr", "sum")
        )
    )

    channel_long = channel_df.melt(
        id_vars="sales_channel",
        value_vars=["Revenue", "Profit"],
        var_name="Metric",
        value_name="LKR"
    )

    fig_channel = px.bar(
        channel_long,
        x="sales_channel",
        y="LKR",
        color="Metric",
        barmode="group",
        title="Revenue and Profit by Sales Channel",
        labels={
            "sales_channel": "Sales Channel",
            "LKR": "Amount (LKR)"
        }
    )

    st.plotly_chart(
        fig_channel,
        use_container_width=True
    )



with row3_col2:

    fig_relationship = px.scatter(
        filtered_df,
        x="revenue_lkr",
        y="profit_lkr",
        color="product_category",
        size="units",
        hover_data=[
            "order_id",
            "product_name",
            "province",
            "sales_channel",
            "customer_rating"
        ],
        title="Revenue vs Profit Relationship",
        labels={
            "revenue_lkr": "Revenue (LKR)",
            "profit_lkr": "Profit (LKR)",
            "product_category": "Product Category"
        },
        opacity=0.7
    )

    st.plotly_chart(
        fig_relationship,
        use_container_width=True
    )




st.subheader(" Return Rate by Product Category")

return_df = (
    filtered_df
    .groupby("product_category")
    .agg(
        Total_Orders=("returned", "size"),
        Returned_Orders=(
            "returned",
            lambda x: (x == "Yes").sum()
        )
    )
    .reset_index()
)

return_df["Return Rate"] = (
    return_df["Returned_Orders"]
    / return_df["Total_Orders"]
    * 100
)

return_df = return_df.sort_values(
    "Return Rate",
    ascending=False
)

fig_return = px.bar(
    return_df,
    x="product_category",
    y="Return Rate",
    title="Return Rate by Product Category",
    labels={
        "product_category": "Product Category",
        "Return Rate": "Return Rate (%)"
    },
    text=return_df["Return Rate"].round(2)
)

fig_return.update_traces(
    texttemplate="%{text}%",
    textposition="outside"
)

st.plotly_chart(
    fig_return,
    use_container_width=True
)




st.subheader("🏆 Top 10 Products by Revenue")

top_products = (
    filtered_df
    .groupby("product_name", as_index=False)
    .agg(
        Revenue=("revenue_lkr", "sum"),
        Profit=("profit_lkr", "sum"),
        Units=("units", "sum")
    )
    .sort_values(
        "Revenue",
        ascending=False
    )
    .head(10)
)

fig_products = px.bar(
    top_products.sort_values("Revenue"),
    x="Revenue",
    y="product_name",
    orientation="h",
    title="Top 10 Products by Revenue",
    labels={
        "product_name": "Product",
        "Revenue": "Revenue (LKR)"
    },
    text_auto=".2s"
)

st.plotly_chart(
    fig_products,
    use_container_width=True
)




row5_col1, row5_col2 = st.columns(2)


with row5_col1:

    delivery_df = (
        filtered_df["delivery_performance"]
        .value_counts()
        .reset_index()
    )

    delivery_df.columns = [
        "Delivery Performance",
        "Orders"
    ]

    fig_delivery = px.pie(
        delivery_df,
        names="Delivery Performance",
        values="Orders",
        title="Delivery Performance Distribution"
    )

    st.plotly_chart(
        fig_delivery,
        use_container_width=True
    )




with row5_col2:

    fig_rating = px.histogram(
        filtered_df,
        x="customer_rating",
        nbins=5,
        title="Customer Rating Distribution",
        labels={
            "customer_rating": "Customer Rating"
        }
    )

    st.plotly_chart(
        fig_rating,
        use_container_width=True
    )




st.subheader("📋 Detailed Transaction View")

display_columns = [
    "order_id",
    "order_date",
    "province",
    "city",
    "sales_channel",
    "customer_segment",
    "product_category",
    "product_name",
    "units",
    "unit_price_lkr",
    "discount_pct",
    "revenue_lkr",
    "cost_lkr",
    "profit_lkr",
    "payment_method",
    "delivery_days",
    "customer_rating",
    "returned",
    "promotion"
]

available_columns = [
    column
    for column in display_columns
    if column in filtered_df.columns
]

table_df = filtered_df[available_columns].copy()

st.dataframe(
    table_df,
    use_container_width=True,
    hide_index=True
)



st.markdown("---")

st.subheader("💡 Evidence-Based Management Insights")


if not filtered_df.empty:


    province_analysis = (
        filtered_df
        .groupby("province")["revenue_lkr"]
        .sum()
        .sort_values(ascending=False)
    )

    highest_province = province_analysis.index[0]

    highest_province_revenue = province_analysis.iloc[0]


    category_analysis = (
        filtered_df
        .groupby("product_category")["revenue_lkr"]
        .sum()
        .sort_values(ascending=False)
    )

    highest_category = category_analysis.index[0]

    highest_category_revenue = category_analysis.iloc[0]



    return_analysis = (
        filtered_df
        .groupby("product_category")
        .agg(
            total=("returned", "size"),
            returned=("returned", lambda x: (x == "Yes").sum())
        )
    )

    return_analysis["rate"] = (
        return_analysis["returned"]
        / return_analysis["total"]
        * 100
    )

    highest_return_category = return_analysis["rate"].idxmax()

    highest_return_rate = return_analysis["rate"].max()



    channel_analysis = (
        filtered_df
        .groupby("sales_channel")["revenue_lkr"]
        .sum()
        .sort_values(ascending=False)
    )

    best_channel = channel_analysis.index[0]

    best_channel_revenue = channel_analysis.iloc[0]



    st.markdown(
        f"""
        **1. Regional performance:**  
        **{highest_province}** generated the highest revenue among
        the selected provinces, with approximately
        **LKR {highest_province_revenue:,.2f}**.
        Management should ensure adequate stock and fulfilment
        capacity in this market.

        **2. Product opportunity:**  
        **{highest_category}** is the highest-revenue product
        category, generating approximately
        **LKR {highest_category_revenue:,.2f}**.
        This category should be monitored for inventory availability
        and further growth opportunities.

        **3. Return risk:**  
        **{highest_return_category}** has the highest return rate
        at approximately **{highest_return_rate:.2f}%**.
        Management should investigate product quality, customer
        expectations and fulfilment issues in this category.

        **4. Channel performance:**  
        **{best_channel}** generated the highest revenue among the
        available sales channels, at approximately
        **LKR {best_channel_revenue:,.2f}**.
        Management can consider allocating additional marketing
        and operational resources to this channel.
        """
    )


# ============================================================
# 22. MANAGEMENT RECOMMENDATIONS
# ============================================================

st.subheader(" Recommended Management Actions")

st.markdown(
    f"""
    **Recommendation 1 – Reduce return-related losses:**  
    Investigate the products within **{highest_return_category}**
    with high return frequency. Review product descriptions,
    quality control and fulfilment processes before increasing
    promotional spending.

    **Recommendation 2 – Prioritise high-performing markets and channels:**  
    Continue monitoring **{highest_province}** and the
    **{best_channel}** sales channel. Management should consider
    improving stock availability and targeted marketing in these
    areas while monitoring profitability rather than revenue alone.
    """
)



with st.expander(" Analysis Limitations"):

    st.markdown(
        """
        - The dataset is synthetic and represents a limited period
          from January to June 2026.
        - Customer ratings contain missing values and median
          imputation may not perfectly represent the original ratings.
        - Revenue and profit analysis is based on the supplied
          transaction-level fields and does not include broader
          business costs such as marketing or overhead costs.
        - The dashboard identifies relationships and patterns but
          does not establish causal relationships.
        """
    )



st.markdown("---")

st.caption(
    "CIT308 Data Visualization | LankaMart Retail Dashboard | "
    "Developed using Python, Pandas, Plotly and Streamlit"
)