import streamlit as st
import json
import os
import uuid
from datetime import datetime, date
from pathlib import Path

import pandas as pd
import plotly.express as px


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="💰 Smart Expense Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

DATA_DIR = Path("data")
EXPENSE_FILE = DATA_DIR / "expenses.json"
SETTINGS_FILE = DATA_DIR / "settings.json"


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>
    .main {
        background-color: #f7f9fc;
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    .app-title {
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 0;
    }

    .subtitle {
        color: #667085;
        font-size: 17px;
        margin-bottom: 25px;
    }

    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 3px 12px rgba(0,0,0,0.06);
        border: 1px solid #eaecf0;
    }

    .success-box {
        padding: 15px;
        border-radius: 12px;
        background: #ecfdf3;
        border: 1px solid #abefc6;
    }

    .warning-box {
        padding: 15px;
        border-radius: 12px;
        background: #fffaeb;
        border: 1px solid #fedf89;
    }

    .danger-box {
        padding: 15px;
        border-radius: 12px;
        background: #fef3f2;
        border: 1px solid #fecdca;
    }

    div[data-testid="stMetric"] {
        background-color: white;
        border-radius: 14px;
        padding: 15px;
        border: 1px solid #eaecf0;
    }

    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# FILE / JSON FUNCTIONS
# ============================================================

def ensure_files():
    """Create data folder and JSON files if they don't exist."""

    DATA_DIR.mkdir(exist_ok=True)

    if not EXPENSE_FILE.exists():
        EXPENSE_FILE.write_text("[]", encoding="utf-8")

    if not SETTINGS_FILE.exists():
        default_settings = {
            "daily_limit": 1000.0,
            "currency": "₹",
            "warning_percentage": 80
        }

        SETTINGS_FILE.write_text(
            json.dumps(default_settings, indent=4),
            encoding="utf-8"
        )


def load_json(file_path, default):
    """Safely load JSON data."""

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)

    except (json.JSONDecodeError, FileNotFoundError):
        return default


def save_json(file_path, data):
    """Save data into JSON."""

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def load_expenses():
    return load_json(EXPENSE_FILE, [])


def save_expenses(expenses):
    save_json(EXPENSE_FILE, expenses)


def load_settings():
    return load_json(
        SETTINGS_FILE,
        {
            "daily_limit": 1000.0,
            "currency": "₹",
            "warning_percentage": 80
        }
    )


def save_settings(settings):
    save_json(SETTINGS_FILE, settings)


# ============================================================
# SESSION STATE
# ============================================================

def initialize_session():

    if "expenses" not in st.session_state:
        st.session_state.expenses = load_expenses()

    if "settings" not in st.session_state:
        st.session_state.settings = load_settings()

    if "editing_id" not in st.session_state:
        st.session_state.editing_id = None

    if "page" not in st.session_state:
        st.session_state.page = "Dashboard"


ensure_files()
initialize_session()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def refresh_data():
    st.session_state.expenses = load_expenses()
    st.session_state.settings = load_settings()


def generate_id():
    return str(uuid.uuid4())[:8].upper()


def get_today_expenses():
    today = date.today().isoformat()

    return [
        expense
        for expense in st.session_state.expenses
        if expense["date"] == today
    ]


def get_today_total():
    return sum(
        float(expense["amount"])
        for expense in get_today_expenses()
    )


def currency():
    return st.session_state.settings.get("currency", "₹")


def format_money(amount):
    return f"{currency()}{amount:,.2f}"


def expenses_dataframe():

    expenses = st.session_state.expenses

    if not expenses:
        return pd.DataFrame(
            columns=[
                "id",
                "date",
                "time",
                "amount",
                "category",
                "description",
                "payment_method"
            ]
        )

    df = pd.DataFrame(expenses)

    df["amount"] = pd.to_numeric(
        df["amount"],
        errors="coerce"
    )

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    return df


# ============================================================
# DAILY LIMIT ALERT
# ============================================================

def show_daily_alert():

    today_total = get_today_total()

    daily_limit = float(
        st.session_state.settings.get(
            "daily_limit",
            1000
        )
    )

    warning_percentage = float(
        st.session_state.settings.get(
            "warning_percentage",
            80
        )
    )

    if daily_limit <= 0:
        return

    percentage = (today_total / daily_limit) * 100

    if today_total > daily_limit:

        exceeded = today_total - daily_limit

        st.markdown(
            f"""
            <div class="danger-box">
                <h3>🚨 Daily Limit Exceeded!</h3>
                <b>Today's spending:</b> {format_money(today_total)}<br>
                <b>Daily limit:</b> {format_money(daily_limit)}<br>
                <b>Exceeded by:</b> {format_money(exceeded)}
            </div>
            """,
            unsafe_allow_html=True
        )

    elif percentage >= warning_percentage:

        remaining = daily_limit - today_total

        st.markdown(
            f"""
            <div class="warning-box">
                <h3>⚠️ Approaching Daily Limit</h3>
                You have spent <b>{percentage:.0f}%</b> of today's budget.<br>
                Remaining: <b>{format_money(remaining)}</b>
            </div>
            """,
            unsafe_allow_html=True
        )

    else:

        remaining = daily_limit - today_total

        st.markdown(
            f"""
            <div class="success-box">
                <b>🟢 Daily Budget Status:</b>
                {format_money(remaining)} remaining today.
            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## 💰 Expense Tracker")

    st.caption("Simple • Smart • Local")

    st.divider()

    pages = [
        "Dashboard",
        "Add Expense",
        "Transactions",
        "Analytics",
        "Budget",
        "Settings"
    ]

    selected_page = st.radio(
        "Navigation",
        pages,
        index=pages.index(st.session_state.page)
    )

    st.session_state.page = selected_page

    st.divider()

    today_total = get_today_total()

    st.metric(
        "Today's Spending",
        format_money(today_total)
    )

    st.metric(
        "Daily Limit",
        format_money(
            st.session_state.settings["daily_limit"]
        )
    )

    st.divider()

    st.caption("📁 Storage")
    st.caption("Local JSON files")
    st.caption("No database required")


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="app-title">💰 Smart Expense Tracker</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Track your money, understand your spending, and stay within budget.'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# GLOBAL DAILY ALERT
# ============================================================

show_daily_alert()

st.write("")


# ============================================================
# DASHBOARD
# ============================================================

if st.session_state.page == "Dashboard":

    df = expenses_dataframe()

    total_expense = (
        float(df["amount"].sum())
        if not df.empty
        else 0
    )

    today_total = get_today_total()

    transaction_count = len(st.session_state.expenses)

    highest_expense = (
        float(df["amount"].max())
        if not df.empty
        else 0
    )

    daily_limit = float(
        st.session_state.settings["daily_limit"]
    )

    remaining = daily_limit - today_total

    # -------------------------------
    # Metrics
    # -------------------------------

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.metric(
            "💸 Total Spending",
            format_money(total_expense)
        )

    with c2:
        st.metric(
            "📅 Today",
            format_money(today_total)
        )

    with c3:
        st.metric(
            "🧾 Transactions",
            transaction_count
        )

    with c4:
        st.metric(
            "🔥 Highest Expense",
            format_money(highest_expense)
        )

    with c5:

        if remaining >= 0:
            st.metric(
                "💰 Remaining",
                format_money(remaining)
            )
        else:
            st.metric(
                "🚨 Over Budget",
                format_money(abs(remaining))
            )

    st.write("")

    # -------------------------------
    # Budget Progress
    # -------------------------------

    st.subheader("🎯 Today's Budget")

    if daily_limit > 0:

        progress = min(
            today_total / daily_limit,
            1.0
        )

        st.progress(progress)

        percentage = (
            today_total / daily_limit
        ) * 100

        st.write(
            f"**{format_money(today_total)}** "
            f"of **{format_money(daily_limit)}** "
            f"used ({percentage:.1f}%)"
        )

    st.divider()

    # -------------------------------
    # Charts
    # -------------------------------

    if not df.empty:

        col1, col2 = st.columns(2)

        with col1:

            st.subheader("🍕 Spending by Category")

            category_data = (
                df.groupby("category")["amount"]
                .sum()
                .reset_index()
            )

            fig = px.pie(
                category_data,
                names="category",
                values="amount",
                hole=0.45
            )

            fig.update_layout(
                margin=dict(
                    t=20,
                    b=20,
                    l=20,
                    r=20
                )
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        with col2:

            st.subheader("📈 Spending Trend")

            daily_data = (
                df.groupby("date")["amount"]
                .sum()
                .reset_index()
            )

            daily_data = daily_data.sort_values("date")

            fig = px.line(
                daily_data,
                x="date",
                y="amount",
                markers=True
            )

            fig.update_layout(
                xaxis_title="Date",
                yaxis_title=f"Amount ({currency()})"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        # -------------------------------
        # Recent Transactions
        # -------------------------------

        st.subheader("🕒 Recent Transactions")

        recent = df.sort_values(
            "date",
            ascending=False
        ).head(5)

        display_df = recent.copy()

        display_df["date"] = (
            display_df["date"]
            .dt.strftime("%d-%m-%Y")
        )

        display_df["amount"] = (
            display_df["amount"]
            .map(lambda x: format_money(x))
        )

        display_df = display_df[
            [
                "date",
                "time",
                "category",
                "description",
                "amount",
                "payment_method"
            ]
        ]

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "👋 No expenses yet. "
            "Go to **Add Expense** to record your first expense."
        )


# ============================================================
# ADD EXPENSE
# ============================================================

elif st.session_state.page == "Add Expense":

    st.subheader("➕ Add New Expense")

    with st.form("add_expense_form"):

        col1, col2 = st.columns(2)

        with col1:

            expense_date = st.date_input(
                "📅 Date",
                value=date.today()
            )

            amount = st.number_input(
                f"💰 Amount ({currency()})",
                min_value=0.01,
                step=10.0,
                format="%.2f"
            )

            category = st.selectbox(
                "🏷️ Category",
                [
                    "Food",
                    "Travel",
                    "Shopping",
                    "Bills",
                    "Education",
                    "Entertainment",
                    "Health",
                    "Groceries",
                    "Rent",
                    "Other"
                ]
            )

        with col2:

            payment_method = st.selectbox(
                "💳 Payment Method",
                [
                    "UPI",
                    "Cash",
                    "Debit Card",
                    "Credit Card",
                    "Bank Transfer",
                    "Other"
                ]
            )

            description = st.text_input(
                "📝 Description",
                placeholder="Example: Lunch at college"
            )

            expense_time = st.time_input(
                "⏰ Time",
                value=datetime.now().time()
            )

        submitted = st.form_submit_button(
            "➕ Add Expense",
            use_container_width=True
        )

        if submitted:

            if amount <= 0:

                st.error(
                    "Amount must be greater than zero."
                )

            else:

                new_expense = {
                    "id": generate_id(),
                    "date": expense_date.isoformat(),
                    "time": expense_time.strftime("%H:%M"),
                    "amount": float(amount),
                    "category": category,
                    "description": description.strip()
                    if description.strip()
                    else "No description",
                    "payment_method": payment_method
                }

                st.session_state.expenses.append(
                    new_expense
                )

                save_expenses(
                    st.session_state.expenses
                )

                st.success(
                    "✅ Expense added successfully!"
                )

                st.rerun()


# ============================================================
# TRANSACTIONS
# ============================================================

elif st.session_state.page == "Transactions":

    st.subheader("📋 All Transactions")

    if not st.session_state.expenses:

        st.info(
            "No transactions available."
        )

    else:

        df = expenses_dataframe()

        # -------------------------------
        # Search
        # -------------------------------

        search = st.text_input(
            "🔎 Search expenses",
            placeholder="Search by description or category..."
        )

        if search:

            search_lower = search.lower()

            mask = (
                df["description"]
                .astype(str)
                .str.lower()
                .str.contains(search_lower)
                |
                df["category"]
                .astype(str)
                .str.lower()
                .str.contains(search_lower)
            )

            df = df[mask]

        # -------------------------------
        # Filters
        # -------------------------------

        col1, col2, col3 = st.columns(3)

        with col1:

            categories = [
                "All"
            ] + sorted(
                df["category"].dropna().unique().tolist()
            )

            selected_category = st.selectbox(
                "Category",
                categories
            )

        with col2:

            payment_methods = [
                "All"
            ] + sorted(
                df["payment_method"]
                .dropna()
                .unique()
                .tolist()
            )

            selected_payment = st.selectbox(
                "Payment Method",
                payment_methods
            )

        with col3:

            sort_order = st.selectbox(
                "Sort",
                [
                    "Newest First",
                    "Oldest First",
                    "Highest Amount",
                    "Lowest Amount"
                ]
            )

        if selected_category != "All":

            df = df[
                df["category"]
                == selected_category
            ]

        if selected_payment != "All":

            df = df[
                df["payment_method"]
                == selected_payment
            ]

        if sort_order == "Newest First":

            df = df.sort_values(
                ["date", "time"],
                ascending=False
            )

        elif sort_order == "Oldest First":

            df = df.sort_values(
                ["date", "time"],
                ascending=True
            )

        elif sort_order == "Highest Amount":

            df = df.sort_values(
                "amount",
                ascending=False
            )

        else:

            df = df.sort_values(
                "amount",
                ascending=True
            )

        st.write(
            f"Showing **{len(df)}** transaction(s)"
        )

        # -------------------------------
        # Transaction Cards
        # -------------------------------

        for _, row in df.iterrows():

            with st.container(border=True):

                col1, col2, col3, col4 = st.columns(
                    [1.2, 2, 2, 1.5]
                )

                with col1:

                    st.write(
                        f"📅 {row['date'].strftime('%d-%m-%Y')}"
                    )

                    st.caption(
                        f"⏰ {row['time']}"
                    )

                with col2:

                    st.write(
                        f"**{row['category']}**"
                    )

                    st.caption(
                        row["description"]
                    )

                with col3:

                    st.write(
                        f"💳 {row['payment_method']}"
                    )

                    st.write(
                        f"### {format_money(row['amount'])}"
                    )

                with col4:

                    if st.button(
                        "✏️ Edit",
                        key=f"edit_{row['id']}"
                    ):

                        st.session_state.editing_id = row["id"]

                    if st.button(
                        "🗑️ Delete",
                        key=f"delete_{row['id']}"
                    ):

                        st.session_state.expenses = [
                            expense
                            for expense
                            in st.session_state.expenses
                            if expense["id"] != row["id"]
                        ]

                        save_expenses(
                            st.session_state.expenses
                        )

                        st.success(
                            "Expense deleted."
                        )

                        st.rerun()

        # -------------------------------
        # Edit Form
        # -------------------------------

        if st.session_state.editing_id:

            expense = next(
                (
                    e for e
                    in st.session_state.expenses
                    if e["id"]
                    == st.session_state.editing_id
                ),
                None
            )

            if expense:

                st.divider()

                st.subheader("✏️ Edit Expense")

                with st.form("edit_expense_form"):

                    col1, col2 = st.columns(2)

                    with col1:

                        edit_date = st.date_input(
                            "Date",
                            value=datetime.strptime(
                                expense["date"],
                                "%Y-%m-%d"
                            ).date()
                        )

                        edit_amount = st.number_input(
                            "Amount",
                            min_value=0.01,
                            value=float(
                                expense["amount"]
                            ),
                            step=10.0
                        )

                        edit_category = st.selectbox(
                            "Category",
                            [
                                "Food",
                                "Travel",
                                "Shopping",
                                "Bills",
                                "Education",
                                "Entertainment",
                                "Health",
                                "Groceries",
                                "Rent",
                                "Other"
                            ],
                            index=[
                                "Food",
                                "Travel",
                                "Shopping",
                                "Bills",
                                "Education",
                                "Entertainment",
                                "Health",
                                "Groceries",
                                "Rent",
                                "Other"
                            ].index(
                                expense["category"]
                            )
                        )

                    with col2:

                        edit_payment = st.selectbox(
                            "Payment Method",
                            [
                                "UPI",
                                "Cash",
                                "Debit Card",
                                "Credit Card",
                                "Bank Transfer",
                                "Other"
                            ],
                            index=[
                                "UPI",
                                "Cash",
                                "Debit Card",
                                "Credit Card",
                                "Bank Transfer",
                                "Other"
                            ].index(
                                expense["payment_method"]
                            )
                        )

                        edit_description = st.text_input(
                            "Description",
                            value=expense["description"]
                        )

                    save_edit = st.form_submit_button(
                        "💾 Save Changes",
                        use_container_width=True
                    )

                    if save_edit:

                        for item in st.session_state.expenses:

                            if item["id"] == expense["id"]:

                                item["date"] = (
                                    edit_date.isoformat()
                                )

                                item["amount"] = float(
                                    edit_amount
                                )

                                item["category"] = (
                                    edit_category
                                )

                                item["payment_method"] = (
                                    edit_payment
                                )

                                item["description"] = (
                                    edit_description
                                )

                        save_expenses(
                            st.session_state.expenses
                        )

                        st.session_state.editing_id = None

                        st.success(
                            "✅ Expense updated successfully!"
                        )

                        st.rerun()


# ============================================================
# ANALYTICS
# ============================================================

elif st.session_state.page == "Analytics":

    st.subheader("📊 Spending Analytics")

    df = expenses_dataframe()

    if df.empty:

        st.info(
            "Add some expenses to see analytics."
        )

    else:

        # -------------------------------
        # Category Analysis
        # -------------------------------

        st.subheader("🏷️ Category Analysis")

        category_data = (
            df.groupby("category")["amount"]
            .agg(["sum", "count", "mean"])
            .reset_index()
        )

        category_data.columns = [
            "Category",
            "Total",
            "Transactions",
            "Average"
        ]

        st.dataframe(
            category_data.style.format(
                {
                    "Total": f"{currency()}{{:,.2f}}",
                    "Average": f"{currency()}{{:,.2f}}"
                }
            ),
            use_container_width=True,
            hide_index=True
        )

        col1, col2 = st.columns(2)

        with col1:

            st.subheader("📊 Category Spending")

            fig = px.bar(
                category_data,
                x="Category",
                y="Total",
                text_auto=".2f"
            )

            fig.update_layout(
                yaxis_title=f"Amount ({currency()})"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        with col2:

            st.subheader("💳 Payment Methods")

            payment_data = (
                df.groupby("payment_method")["amount"]
                .sum()
                .reset_index()
            )

            fig = px.pie(
                payment_data,
                names="payment_method",
                values="amount",
                hole=0.4
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        # -------------------------------
        # Monthly Analysis
        # -------------------------------

        st.subheader("📅 Monthly Spending")

        df["month"] = df["date"].dt.to_period(
            "M"
        ).astype(str)

        monthly = (
            df.groupby("month")["amount"]
            .sum()
            .reset_index()
        )

        fig = px.line(
            monthly,
            x="month",
            y="amount",
            markers=True
        )

        fig.update_layout(
            xaxis_title="Month",
            yaxis_title=f"Amount ({currency()})"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        # -------------------------------
        # Insights
        # -------------------------------

        st.subheader("💡 Spending Insights")

        highest_category = (
            category_data
            .sort_values(
                "Total",
                ascending=False
            )
            .iloc[0]
        )

        average_expense = df["amount"].mean()

        ic1, ic2, ic3 = st.columns(3)

        with ic1:

            st.metric(
                "Most Expensive Category",
                highest_category["Category"]
            )

        with ic2:

            st.metric(
                "Category Spending",
                format_money(
                    highest_category["Total"]
                )
            )

        with ic3:

            st.metric(
                "Average Transaction",
                format_money(
                    average_expense
                )
            )


# ============================================================
# BUDGET
# ============================================================

elif st.session_state.page == "Budget":

    st.subheader("🎯 Budget Manager")

    daily_limit = float(
        st.session_state.settings["daily_limit"]
    )

    today_total = get_today_total()

    st.metric(
        "Today's Spending",
        format_money(today_total)
    )

    st.metric(
        "Daily Limit",
        format_money(daily_limit)
    )

    if daily_limit > 0:

        progress = min(
            today_total / daily_limit,
            1
        )

        st.progress(progress)

    st.divider()

    st.subheader("📅 Daily Budget Status")

    if today_total > daily_limit:

        st.error(
            f"🚨 You exceeded your budget by "
            f"{format_money(today_total - daily_limit)}"
        )

    else:

        st.success(
            f"🟢 You have "
            f"{format_money(daily_limit - today_total)} "
            f"remaining today."
        )

    st.divider()

    st.subheader("📊 Budget Tips")

    if daily_limit > 0:

        remaining = daily_limit - today_total

        if remaining < 0:

            st.warning(
                "Try to reduce unnecessary spending "
                "for the rest of today."
            )

        elif remaining < daily_limit * 0.2:

            st.warning(
                "You are close to your daily spending limit."
            )

        else:

            st.info(
                "You are within your daily budget. 👍"
            )


# ============================================================
# SETTINGS
# ============================================================

elif st.session_state.page == "Settings":

    st.subheader("⚙️ Settings")

    settings = st.session_state.settings

    with st.form("settings_form"):

        new_limit = st.number_input(
            "💰 Daily Expense Limit",
            min_value=0.0,
            value=float(
                settings.get(
                    "daily_limit",
                    1000
                )
            ),
            step=100.0
        )

        new_currency = st.selectbox(
            "Currency",
            [
                "₹",
                "$",
                "€",
                "£",
                "¥"
            ],
            index=[
                "₹",
                "$",
                "€",
                "£",
                "¥"
            ].index(
                settings.get(
                    "currency",
                    "₹"
                )
            )
        )

        warning_percentage = st.slider(
            "⚠️ Warning when budget reaches",
            min_value=50,
            max_value=95,
            value=int(
                settings.get(
                    "warning_percentage",
                    80
                )
            ),
            step=5
        )

        save_settings_button = st.form_submit_button(
            "💾 Save Settings",
            use_container_width=True
        )

        if save_settings_button:

            st.session_state.settings = {
                "daily_limit": float(new_limit),
                "currency": new_currency,
                "warning_percentage": warning_percentage
            }

            save_settings(
                st.session_state.settings
            )

            st.success(
                "✅ Settings saved successfully!"
            )

            st.rerun()

    st.divider()

    # -------------------------------
    # Export
    # -------------------------------

    st.subheader("📤 Export Data")

    df = expenses_dataframe()

    if not df.empty:

        export_df = df.copy()

        export_df["date"] = (
            export_df["date"]
            .dt.strftime("%Y-%m-%d")
        )

        csv_data = export_df.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            label="📥 Download Expenses as CSV",
            data=csv_data,
            file_name="expenses.csv",
            mime="text/csv",
            use_container_width=True
        )

    else:

        st.info(
            "No expenses available for export."
        )

    st.divider()

    # -------------------------------
    # Backup
    # -------------------------------

    st.subheader("💾 Backup")

    backup_data = json.dumps(
        st.session_state.expenses,
        indent=4
    )

    st.download_button(
        "📦 Download JSON Backup",
        data=backup_data,
        file_name="expenses_backup.json",
        mime="application/json",
        use_container_width=True
    )

    st.divider()

    # -------------------------------
    # Import
    # -------------------------------

    st.subheader("📥 Restore JSON Backup")

    uploaded_file = st.file_uploader(
        "Upload expenses JSON file",
        type=["json"]
    )

    if uploaded_file:

        try:

            imported_data = json.load(
                uploaded_file
            )

            if isinstance(
                imported_data,
                list
            ):

                st.session_state.expenses = (
                    imported_data
                )

                save_expenses(
                    imported_data
                )

                st.success(
                    "✅ Backup restored successfully!"
                )

            else:

                st.error(
                    "Invalid JSON backup format."
                )

        except json.JSONDecodeError:

            st.error(
                "The uploaded file is not valid JSON."
            )

    st.divider()

    # -------------------------------
    # Reset Data
    # -------------------------------

    st.subheader("⚠️ Danger Zone")

    st.warning(
        "Deleting all expenses cannot be undone "
        "unless you have a backup."
    )

    if st.button(
        "🗑️ Delete All Expenses",
        use_container_width=True
    ):

        st.session_state.expenses = []

        save_expenses([])

        st.success(
            "All expenses have been deleted."
        )

        st.rerun()


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "💰 Smart Expense Tracker • "
    "Built with Python + Streamlit + JSON + Plotly"
)