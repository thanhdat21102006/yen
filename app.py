import streamlit as st
import psycopg2
import os
from datetime import datetime

st.set_page_config(page_title="Yến Manager Pro", layout="wide")

# ===== CONNECT DATABASE =====
DATABASE_URL = os.getenv("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# ===== SIDEBAR =====
st.sidebar.title("🪺 Yến Manager PRO")
menu = st.sidebar.radio(
    "Chọn chức năng",
    ["📊 Dashboard", "👥 Khách hàng", "📦 Sản phẩm", "💰 Bán hàng"]
)

# ===== DASHBOARD =====
if menu == "📊 Dashboard":
    st.title("📊 Tổng Quan")

    cur.execute("SELECT COALESCE(SUM(total),0) FROM sales")
    revenue = cur.fetchone()[0]

    cur.execute("SELECT COALESCE(SUM(total_debt),0) FROM customers")
    debt = cur.fetchone()[0]

    cur.execute("SELECT COALESCE(SUM(stock),0) FROM products")
    stock = cur.fetchone()[0]

    col1, col2, col3 = st.columns(3)

    col1.metric("💰 Doanh thu", f"{revenue:,.0f} đ")
    col2.metric("🧾 Công nợ", f"{debt:,.0f} đ")
    col3.metric("📦 Tồn kho", stock)

# ===== CUSTOMERS =====
elif menu == "👥 Khách hàng":
    st.title("👥 Quản lý khách hàng")

    name = st.text_input("Tên khách")
    phone = st.text_input("SĐT")

    if st.button("Thêm khách"):
        cur.execute(
            "INSERT INTO customers(name, phone) VALUES(%s,%s)",
            (name, phone)
        )
        conn.commit()
        st.success("Đã thêm khách")

    cur.execute("SELECT id,name,phone,total_debt FROM customers")
    data = cur.fetchall()
    st.dataframe(data, use_container_width=True)

# ===== PRODUCTS =====
elif menu == "📦 Sản phẩm":
    st.title("📦 Quản lý sản phẩm")

    name = st.text_input("Tên sản phẩm")
    price = st.number_input("Giá bán", min_value=0.0)
    stock = st.number_input("Số lượng tồn", min_value=0)

    if st.button("Thêm sản phẩm"):
        cur.execute(
            "INSERT INTO products(name,price,stock) VALUES(%s,%s,%s)",
            (name, price, stock)
        )
        conn.commit()
        st.success("Đã thêm sản phẩm")

    cur.execute("SELECT id,name,price,stock FROM products")
    data = cur.fetchall()
    st.dataframe(data, use_container_width=True)

# ===== SALES =====
elif menu == "💰 Bán hàng":
    st.title("💰 Bán hàng")

    cur.execute("SELECT id,name FROM customers")
    customers = cur.fetchall()

    cur.execute("SELECT id,name,price,stock FROM products")
    products = cur.fetchall()

    if customers and products:
        customer_dict = {c[1]: c[0] for c in customers}
        product_dict = {p[1]: p for p in products}

        customer_name = st.selectbox("Chọn khách", list(customer_dict.keys()))
        product_name = st.selectbox("Chọn sản phẩm", list(product_dict.keys()))

        quantity = st.number_input("Số lượng", min_value=1)

        price = product_dict[product_name][2]
        stock = product_dict[product_name][3]

        total = price * quantity
        st.write(f"Tổng tiền: {total:,.0f} đ")

        paid = st.number_input("Khách trả", min_value=0.0)
        debt = total - paid

        if st.button("Xác nhận"):
            if quantity > stock:
                st.error("Không đủ hàng")
            else:
                customer_id = customer_dict[customer_name]
                product_id = product_dict[product_name][0]

                cur.execute(
                    """INSERT INTO sales(customer_id,product_id,quantity,total,paid,debt)
                       VALUES(%s,%s,%s,%s,%s,%s)""",
                    (customer_id, product_id, quantity, total, paid, debt)
                )

                cur.execute(
                    "UPDATE products SET stock=stock-%s WHERE id=%s",
                    (quantity, product_id)
                )

                cur.execute(
                    "UPDATE customers SET total_debt=total_debt+%s WHERE id=%s",
                    (debt, customer_id)
                )

                conn.commit()
                st.success("Bán thành công!")
