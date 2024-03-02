import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency
from PIL import Image
sns.set(style='dark')

def create_daily_orders_df(df):
    daily_orders_df = df.resample(rule='D', on='order_purchase_timestamp').agg({
        "order_id": "nunique",
        "total_price": "sum",
        "review_score": "mean"
    })
    daily_orders_df = daily_orders_df.reset_index()
    daily_orders_df.rename(columns={
        "order_id": "order_count",
        "total_price": "revenue",
        "review_score": "avg_score"
    }, inplace=True)
    
    return daily_orders_df

def create_sum_order_items_df(df):
    sum_order_items_df = df.groupby("product_category_name_english").order_item_id.sum().sort_values(ascending=False).reset_index()
    return sum_order_items_df

def create_seller_df(df):
    seller_df = df.groupby("seller_city").total_price.sum().sort_values(ascending=False).reset_index()
    return seller_df

def create_rate_product_df(df):
    rate_product_df = df.groupby("product_category_name_english")['review_score'].agg('mean').sort_values(ascending=False).reset_index()
    return rate_product_df

def create_bystate_df(df):
    bystate_df = df.groupby(by="seller_state").customer_id.nunique().reset_index()
    bystate_df.rename(columns={
        "customer_id": "customer_count"
    }, inplace=True)
    
    return bystate_df


def create_rfm_df(df):
    rfm_df = df.groupby(by="customer_unique_id", as_index=False).agg({
        "order_purchase_timestamp": "max", #mengambil tanggal order terakhir
        "order_id": "nunique",
        "total_price": "sum"
    })
    rfm_df.columns = ["customer_unique_id", "max_order_timestamp", "frequency", "monetary"]
    
    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"].dt.date
    recent_date = df["order_purchase_timestamp"].dt.date.max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days)
    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)
    
    return rfm_df

all_df = pd.read_csv("all_data.csv")

datetime_columns = ["order_purchase_timestamp", "order_delivered_customer_date"]
all_df.sort_values(by="order_purchase_timestamp", inplace=True)
all_df.reset_index(inplace=True)
 
for column in datetime_columns:
    all_df[column] = pd.to_datetime(all_df[column])

# filter data
min_date = all_df["order_purchase_timestamp"].min()
max_date = all_df["order_purchase_timestamp"].max()
 
with st.sidebar:
    # Menambahkan gambar
    st.image("gambar.png")
    
    # Mengambil start_date & end_date dari date_input
    start_date, end_date = st.date_input(
        label='Filter Data',min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

main_df = all_df[(all_df["order_purchase_timestamp"] >= str(start_date)) & 
                (all_df["order_purchase_timestamp"] <= str(end_date))]


daily_orders_df = create_daily_orders_df(main_df)
sum_order_items_df = create_sum_order_items_df(main_df)
seller_df = create_seller_df(main_df)
rate_product_df = create_rate_product_df(main_df)
bystate_df = create_bystate_df(main_df)
rfm_df = create_rfm_df(main_df)

st.header('E-Commerce Dashboard 🛒')

st.subheader('Daily Orders')
 
col1, col2, col3 = st.columns(3)
 
with col1:
    total_revenue = format_currency(daily_orders_df.revenue.sum(), "$ ", locale='es_CO') 
    st.metric("Total Revenue", value=total_revenue)
 
with col2:
    total_orders = format_currency(daily_orders_df.order_count.sum(), "📊 ")
    st.metric("Total orders", value=total_orders)

with col3:
    avg_orders = format_currency(daily_orders_df.avg_score.mean().round(2), "⭐️ ")
    st.metric("Average Rating", value=avg_orders)
 
fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(
    daily_orders_df["order_purchase_timestamp"],
    daily_orders_df["order_count"],
    marker='o', 
    linewidth=2,
    color="#1C4C7C"
)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)
 
st.pyplot(fig)

st.subheader("Product types with the most and least number of summations")

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(20, 10))

custom_palette = sns.color_palette("Blues", n_colors=10)[::-1]

sns.barplot(x="order_item_id", y="product_category_name_english", data=sum_order_items_df.head(10), palette=custom_palette, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel(None)
ax[0].set_title("Top Selling Products", loc="center", fontsize=18)
ax[0].tick_params(axis ='y', labelsize=15)

sns.barplot(x="order_item_id", y="product_category_name_english", data=sum_order_items_df.sort_values(by="order_item_id", ascending=True).head(10), palette=custom_palette, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel(None)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Least Selling Product", loc="center", fontsize=18)
ax[1].tick_params(axis='y', labelsize=15)

st.pyplot(fig)


st.subheader("Top 10 Products by Average Review Score")
st.set_option('deprecation.showPyplotGlobalUse', False)
rate_product_df.head(10)
top_10_products = rate_product_df.head(10)

# Menggantikan plt.figure dengan plt.subplots
fig, ax = plt.subplots(figsize=(12, 8))

# Memodifikasi warna palette
custom_palette = sns.color_palette("Blues", n_colors=10)[::-1]
colors = ["#72BCD4"] * 3 + ["#D3D3D3"] * 7  # Sesuaikan dengan jumlah kategori

# Menggunakan barplot dengan axis objek (ax) yang telah dibuat
sns.barplot(x="review_score", y="product_category_name_english", data=top_10_products, palette=custom_palette, ax=ax)

ax.set_xlabel("Average Review Score")
ax.set_ylabel("Product Category")

st.pyplot(fig)


st.subheader("Best and Worst Seller Revenue by city")
seller_df.head(10)
custom_palette = sns.color_palette("Blues", n_colors=10)[::-1]

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(20, 10))

sns.barplot(x="total_price", y="seller_city", data=seller_df.head(10), palette=custom_palette, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel(None)
ax[0].set_title("Best Performing Product", loc="center", fontsize=18)
ax[0].tick_params(axis ='y', labelsize=15)

sns.barplot(x="total_price", y="seller_city", data=seller_df.sort_values(by="total_price", ascending=True).head(10), palette=custom_palette, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel(None)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Worst Performing Product", loc="center", fontsize=18)
ax[1].tick_params(axis='y', labelsize=15)
st.pyplot(fig)


st.subheader("Best Customer Based on RFM Parameters")
 
col1, col2, col3 = st.columns(3)
 
with col1:
    avg_recency = round(rfm_df.recency.mean(), 1)
    st.metric("Average Recency (days)", value=avg_recency)
 
with col2:
    avg_frequency = round(rfm_df.frequency.mean(), 2)
    st.metric("Average Frequency", value=avg_frequency)
 
with col3:
    avg_frequency = format_currency(rfm_df.monetary.mean(), "$ ", locale='es_CO') 
    st.metric("Average Monetary", value=avg_frequency)
 
fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(35, 15))
colors = ["#1C4C7C", "#1C4C7C", "#1C4C7C", "#1C4C7C", "#1C4C7C"]
 
sns.barplot(y="recency", x="customer_unique_id", data=rfm_df.sort_values(by="recency", ascending=True).head(10), palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel("customer_unique_id", fontsize=30)
ax[0].set_title("By Recency (days)", loc="center", fontsize=50)
ax[0].tick_params(axis ='x', labelsize=35)
ax[0].set_xticklabels(ax[0].get_xticklabels(), rotation=45, horizontalalignment='right', fontsize=20)
 
sns.barplot(y="recency", x="customer_unique_id", data=rfm_df.sort_values(by="frequency", ascending=False).head(10), palette=colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel(None)
ax[1].set_title("By Frequency", loc="center", fontsize=50)
ax[1].tick_params(axis='x', labelsize=20)
ax[1].set_xticklabels(ax[1].get_xticklabels(), rotation=45, horizontalalignment='right', fontsize=20)

sns.barplot(y="monetary", x="customer_unique_id", data=rfm_df.sort_values(by="monetary", ascending=False).head(10), palette=colors, ax=ax[2])
ax[2].set_ylabel(None)
ax[2].set_xlabel(None)
ax[2].set_title("By Monetary", loc="center", fontsize=50)
ax[2].tick_params(axis='x', labelsize=20)
ax[2].set_xticklabels(ax[2].get_xticklabels(), rotation=45, horizontalalignment='right', fontsize=20)
 
st.pyplot(fig)


st.caption('Copyright (c) E-Commerce 2024')