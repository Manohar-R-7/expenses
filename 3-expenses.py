import streamlit as st
import pandas as pd
import plotly.express as px
import json
import uuid
from pathlib import Path
from datetime import date, datetime


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Smart Expense Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# FILE LOCATIONS
# =========================================================

DATA_DIR = Path("data")
EXPENSE_FILE = DATA_DIR / "expenses.json"
SETTINGS_FILE = DATA_DIR / "settings.json"


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    /* =====================================================
       GENERAL LAYOUT
       ===================================================== */

    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 1400px;
    }

    /* Main headings */
    h1, h2, h3 {
        color: #f8fafc !important;
    }

    /* Captions */
    [data-testid="stCaptionContainer"] {
        color: #94a3b8 !important;
    }


    /* =====================================================
       METRIC CARDS
       ===================================================== */

    [data-testid="stMetric"] {
        background: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 14px !important;
        padding: 15px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.20);
    }

    [data-testid="stMetricLabel"] {
        color: #cbd5e1 !important;
    }

    [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 25px !important;
        font-weight: 700 !important;
    }

    [data-testid="stMetricDelta"] {
        color: #94a3b8 !important;
    }


    /* =====================================================
       SIDEBAR
       ===================================================== */

    section[data-testid="stSidebar"] {
        background: #20212a;
    }


    /* =====================================================
       BUTTONS
       ===================================================== */

    div.stButton > button {
        border-radius: 9px;
        font-weight: 600;
    }


    /* =====================================================
       ALERT BOXES
       ===================================================== */

    .success-box {
        background: #052e1b;
        border: 1px solid #166534;
        border-radius: 10px;
        padding: 12px;
        color: #bbf7d0;
    }

    .warning-box {
        background: #422006;
        border: 1px solid #a16207;
        border-radius: 10px;
        padding: 12px;
        color: #fef08a;
    }

    .danger-box {
        background: #450a0a;
        border: 1px solid #991b1b;
        border-radius: 10px;
        padding: 12px;
        color: #fecaca;
    }


    /* =====================================================
       EXPENSE CARDS
       ===================================================== */

    .expense-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 12px 16px;
        margin-bottom: 8px;
    }


    /* =====================================================
       PROGRESS BAR
       ===================================================== */

    .stProgress > div > div > div > div {
        border-radius: 10px;
    }


    /* =====================================================
       DATAFRAME
       ===================================================== */

    [data-testid="stDataFrame"] {
        border-radius: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# CREATE DATA FILES
# =========================================================

def initialize_files():

    DATA_DIR.mkdir(exist_ok=True)

    if not EXPENSE_FILE.exists():

        EXPENSE_FILE.write_text(
            "[]",
            encoding="utf-8"
        )

    if not SETTINGS_FILE.exists():

        default_settings = {
            "daily_limit": 1000,
            "currency": "₹",
            "warning_percentage": 80
        }

        SETTINGS_FILE.write_text(
            json.dumps(
                default_settings,
                indent=4
            ),
            encoding="utf-8"
        )


# =========================================================
# JSON FUNCTIONS
# =========================================================

def load_json(file_path, default):

    try:

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except (
        FileNotFoundError,
        json.JSONDecodeError
    ):

        return default


def save_json(file_path, data):

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4
        )


def load_expenses():

    return load_json(
        EXPENSE_FILE,
        []
    )


def save_expenses(expenses):

    save_json(
        EXPENSE_FILE,
        expenses
    )


def load_settings():

    default_settings = {
        "daily_limit": 1000,
        "currency": "₹",
        "warning_percentage": 80
    }

    return load_json(
        SETTINGS_FILE,
        default_settings
    )


def save_settings(settings):

    save_json(
        SETTINGS_FILE,
        settings
    )


# =========================================================
# INITIALIZATION
# =========================================================

initialize_files()


# =========================================================
# SESSION STATE
# =========================================================

if "expenses" not in st.session_state:

    st.session_state.expenses = load_expenses()


if "settings" not in st.session_state:

    st.session_state.settings = load_settings()


if "page" not in st.session_state:

    st.session_state.page = "📊 Dashboard"


if "edit_id" not in st.session_state:

    st.session_state.edit_id = None


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def currency():

    return st.session_state.settings.get(
        "currency",
        "₹"
    )


def money(value):

    return f"{currency()}{float(value):,.2f}"


def generate_id():

    return str(
        uuid.uuid4()
    )[:8].upper()


def today_total():

    today = date.today().isoformat()

    return sum(
        float(expense["amount"])
        for expense in st.session_state.expenses
        if expense["date"] == today
    )


def create_dataframe():

    if not st.session_state.expenses:

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

    df = pd.DataFrame(
        st.session_state.expenses
    )

    df["amount"] = pd.to_numeric(
        df["amount"],
        errors="coerce"
    )

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    return df


def refresh_data():

    st.session_state.expenses = load_expenses()
    st.session_state.settings = load_settings()


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.title("💰 Expense Tracker")

    st.caption(
        "Simple • Fast • Local"
    )

    st.divider()

    selected_page = st.radio(
        "MENU",
        [
            "📊 Dashboard",
            "➕ Add Expense",
            "📋 Transactions",
            "📈 Analytics",
            "🎯 Budget",
            "⚙️ Settings"
        ],
        label_visibility="collapsed"
    )

    st.session_state.page = selected_page

    st.divider()

    st.metric(
        "Today's Spending",
        money(today_total())
    )

    st.metric(
        "Daily Limit",
        money(
            st.session_state.settings[
                "daily_limit"
            ]
        )
    )

    st.divider()

    st.caption("💾 Storage")
    st.caption("Local JSON files")
    st.caption("🗄️ No database")


# =========================================================
# MAIN HEADER
# =========================================================

st.title(
    "💰 Smart Expense Tracker"
)

st.caption(
    "Track expenses • Control your budget • Understand your spending"
)


# =========================================================
# DAILY LIMIT ALERT
# =========================================================

daily_limit = float(
    st.session_state.settings[
        "daily_limit"
    ]
)

spent_today = today_total()

warning_percentage = float(
    st.session_state.settings.get(
        "warning_percentage",
        80
    )
)

if daily_limit > 0:

    usage_percentage = (
        spent_today / daily_limit
    ) * 100

    if usage_percentage >= 100:

        exceeded = (
            spent_today - daily_limit
        )

        st.markdown(
            f"""
            <div class="danger-box">
                🚨 <b>Daily Limit Exceeded!</b><br>
                Today's spending:
                <b>{money(spent_today)}</b><br>
                Daily limit:
                <b>{money(daily_limit)}</b><br>
                Exceeded by:
                <b>{money(exceeded)}</b>
            </div>
            """,
            unsafe_allow_html=True
        )

    elif usage_percentage >= warning_percentage:

        remaining = (
            daily_limit - spent_today
        )

        st.markdown(
            f"""
            <div class="warning-box">
                ⚠️ <b>Approaching Daily Limit</b><br>
                You have used
                <b>{usage_percentage:.0f}%</b>
                of today's budget.<br>
                Remaining:
                <b>{money(remaining)}</b>
            </div>
            """,
            unsafe_allow_html=True
        )


# =========================================================
# DASHBOARD
# =========================================================

if st.session_state.page == "📊 Dashboard":

    st.subheader("📊 Overview")

    df = create_dataframe()

    total_spent = (
        df["amount"].sum()
        if not df.empty
        else 0
    )

    transaction_count = len(df)

    highest_expense = (
        df["amount"].max()
        if not df.empty
        else 0
    )

    # -----------------------------------------------------
    # METRICS
    # -----------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "💸 Total Spent",
            money(total_spent)
        )

    with col2:

        st.metric(
            "📅 Today",
            money(spent_today)
        )

    with col3:

        st.metric(
            "🧾 Transactions",
            transaction_count
        )

    with col4:

        st.metric(
            "🔥 Highest Expense",
            money(highest_expense)
        )

    # -----------------------------------------------------
    # BUDGET
    # -----------------------------------------------------

    st.subheader(
        "🎯 Today's Budget"
    )

    if daily_limit > 0:

        progress = min(
            spent_today / daily_limit,
            1.0
        )

        st.progress(progress)

        st.caption(
            f"{money(spent_today)} used "
            f"of {money(daily_limit)}"
        )

    # -----------------------------------------------------
    # CHARTS
    # -----------------------------------------------------

    if not df.empty:

        st.subheader(
            "📊 Spending Overview"
        )

        chart_col1, chart_col2 = st.columns(2)

        # -------------------------------------------------
        # PIE CHART
        # -------------------------------------------------

        with chart_col1:

            category_data = (
                df.groupby(
                    "category"
                )["amount"]
                .sum()
                .reset_index()
            )

            fig = px.pie(
                category_data,
                names="category",
                values="amount",
                hole=0.45,
                title="🍕 Spending by Category"
            )

            fig.update_layout(
                height=350,
                margin=dict(
                    t=55,
                    b=10,
                    l=10,
                    r=10
                ),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(
                    color="white"
                )
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        # -------------------------------------------------
        # DAILY BAR CHART
        # -------------------------------------------------

        with chart_col2:

            daily_data = (
                df.groupby(
                    "date"
                )["amount"]
                .sum()
                .reset_index()
            )

            fig = px.bar(
                daily_data,
                x="date",
                y="amount",
                title="📅 Daily Spending"
            )

            fig.update_layout(
                height=350,
                margin=dict(
                    t=55,
                    b=10,
                    l=10,
                    r=10
                ),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(
                    color="white"
                ),
                xaxis=dict(
                    title="Date"
                ),
                yaxis=dict(
                    title=f"Amount ({currency()})"
                )
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        # -------------------------------------------------
        # RECENT TRANSACTIONS
        # -------------------------------------------------

        st.subheader(
            "🕒 Recent Transactions"
        )

        recent = df.sort_values(
            ["date", "time"],
            ascending=False
        ).head(5)

        for _, row in recent.iterrows():

            c1, c2, c3, c4 = st.columns(
                [1.3, 2.3, 2, 1.2]
            )

            with c1:

                st.write(
                    row["date"].strftime(
                        "%d-%m-%Y"
                    )
                )

                st.caption(
                    row["time"]
                )

            with c2:

                st.write(
                    f"**{row['category']}**"
                )

                st.caption(
                    row["description"]
                )

            with c3:

                st.write(
                    f"💳 {row['payment_method']}"
                )

            with c4:

                st.write(
                    f"**{money(row['amount'])}**"
                )

    else:

        st.info(
            "👋 No expenses yet. "
            "Go to **Add Expense** to record your first expense."
        )


# =========================================================
# ADD EXPENSE
# =========================================================

elif st.session_state.page == "➕ Add Expense":

    st.subheader(
        "➕ Add New Expense"
    )

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
                value=100.0,
                step=10.0
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
            "💾 Save Expense",
            use_container_width=True
        )

        if submitted:

            new_expense = {

                "id":
                    generate_id(),

                "date":
                    expense_date.isoformat(),

                "time":
                    expense_time.strftime(
                        "%H:%M"
                    ),

                "amount":
                    float(amount),

                "category":
                    category,

                "description":
                    description.strip()
                    or "No description",

                "payment_method":
                    payment_method
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


# =========================================================
# TRANSACTIONS
# =========================================================

elif st.session_state.page == "📋 Transactions":

    st.subheader(
        "📋 Transactions"
    )

    df = create_dataframe()

    if df.empty:

        st.info(
            "No transactions found."
        )

    else:

        # -------------------------------------------------
        # FILTERS
        # -------------------------------------------------

        col1, col2, col3 = st.columns(3)

        with col1:

            search = st.text_input(
                "🔎 Search",
                placeholder="Search expenses..."
            )

        with col2:

            categories = [
                "All"
            ] + sorted(
                df["category"]
                .dropna()
                .unique()
                .tolist()
            )

            category_filter = st.selectbox(
                "🏷️ Category",
                categories
            )

        with col3:

            sort_option = st.selectbox(
                "↕️ Sort",
                [
                    "Newest First",
                    "Oldest First",
                    "Highest Amount",
                    "Lowest Amount"
                ]
            )

        # -------------------------------------------------
        # SEARCH
        # -------------------------------------------------

        if search:

            search_mask = (

                df["description"]
                .astype(str)
                .str.contains(
                    search,
                    case=False,
                    na=False
                )

                |

                df["category"]
                .astype(str)
                .str.contains(
                    search,
                    case=False,
                    na=False
                )
            )

            df = df[search_mask]

        # -------------------------------------------------
        # CATEGORY FILTER
        # -------------------------------------------------

        if category_filter != "All":

            df = df[
                df["category"]
                == category_filter
            ]

        # -------------------------------------------------
        # SORT
        # -------------------------------------------------

        if sort_option == "Newest First":

            df = df.sort_values(
                ["date", "time"],
                ascending=False
            )

        elif sort_option == "Oldest First":

            df = df.sort_values(
                ["date", "time"],
                ascending=True
            )

        elif sort_option == "Highest Amount":

            df = df.sort_values(
                "amount",
                ascending=False
            )

        else:

            df = df.sort_values(
                "amount",
                ascending=True
            )

        st.caption(
            f"Showing {len(df)} transaction(s)"
        )

        # -------------------------------------------------
        # TRANSACTION CARDS
        # -------------------------------------------------

        for _, row in df.iterrows():

            with st.container(
                border=True
            ):

                c1, c2, c3, c4 = st.columns(
                    [1.3, 2.5, 1.5, 1.6]
                )

                with c1:

                    st.write(
                        row["date"].strftime(
                            "%d-%m-%Y"
                        )
                    )

                    st.caption(
                        row["time"]
                    )

                with c2:

                    st.write(
                        f"**{row['category']}**"
                    )

                    st.caption(
                        row["description"]
                    )

                with c3:

                    st.write(
                        f"💳 {row['payment_method']}"
                    )

                with c4:

                    st.write(
                        f"**{money(row['amount'])}**"
                    )

                    edit_col, delete_col = st.columns(2)

                    with edit_col:

                        if st.button(
                            "✏️",
                            key=f"edit_{row['id']}"
                        ):

                            st.session_state.edit_id = (
                                row["id"]
                            )

                            st.rerun()

                    with delete_col:

                        if st.button(
                            "🗑️",
                            key=f"delete_{row['id']}"
                        ):

                            st.session_state.expenses = [

                                expense

                                for expense
                                in st.session_state.expenses

                                if expense["id"]
                                != row["id"]
                            ]

                            save_expenses(
                                st.session_state.expenses
                            )

                            st.success(
                                "Expense deleted."
                            )

                            st.rerun()

        # -------------------------------------------------
        # EDIT EXPENSE
        # -------------------------------------------------

        if st.session_state.edit_id:

            expense = next(
                (
                    item

                    for item
                    in st.session_state.expenses

                    if item["id"]
                    == st.session_state.edit_id
                ),
                None
            )

            if expense:

                st.divider()

                st.subheader(
                    "✏️ Edit Expense"
                )

                categories_list = [
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

                payment_list = [
                    "UPI",
                    "Cash",
                    "Debit Card",
                    "Credit Card",
                    "Bank Transfer",
                    "Other"
                ]

                with st.form(
                    "edit_expense_form"
                ):

                    col1, col2 = st.columns(2)

                    with col1:

                        edit_date = st.date_input(
                            "📅 Date",
                            value=datetime.strptime(
                                expense["date"],
                                "%Y-%m-%d"
                            ).date()
                        )

                        edit_amount = st.number_input(
                            "💰 Amount",
                            min_value=0.01,
                            value=float(
                                expense["amount"]
                            ),
                            step=10.0
                        )

                        edit_category = st.selectbox(
                            "🏷️ Category",
                            categories_list,
                            index=categories_list.index(
                                expense["category"]
                            )
                        )

                    with col2:

                        edit_payment = st.selectbox(
                            "💳 Payment Method",
                            payment_list,
                            index=payment_list.index(
                                expense["payment_method"]
                            )
                        )

                        edit_description = st.text_input(
                            "📝 Description",
                            value=expense["description"]
                        )

                    save_edit = st.form_submit_button(
                        "💾 Update Expense",
                        use_container_width=True
                    )

                    cancel_edit = st.form_submit_button(
                        "❌ Cancel",
                        use_container_width=True
                    )

                    if cancel_edit:

                        st.session_state.edit_id = None

                        st.rerun()

                    if save_edit:

                        for item in st.session_state.expenses:

                            if item["id"] == expense["id"]:

                                item["date"] = (
                                    edit_date.isoformat()
                                )

                                item["amount"] = (
                                    float(edit_amount)
                                )

                                item["category"] = (
                                    edit_category
                                )

                                item["payment_method"] = (
                                    edit_payment
                                )

                                item["description"] = (
                                    edit_description.strip()
                                    or "No description"
                                )

                        save_expenses(
                            st.session_state.expenses
                        )

                        st.session_state.edit_id = None

                        st.success(
                            "✅ Expense updated successfully!"
                        )

                        st.rerun()


# =========================================================
# ANALYTICS
# =========================================================

elif st.session_state.page == "📈 Analytics":

    st.subheader(
        "📈 Spending Analytics"
    )

    df = create_dataframe()

    if df.empty:

        st.info(
            "Add some expenses to see analytics."
        )

    else:

        # -------------------------------------------------
        # CATEGORY DATA
        # -------------------------------------------------

        category_data = (
            df.groupby(
                "category"
            )["amount"]
            .sum()
            .reset_index()
            .sort_values(
                "amount",
                ascending=False
            )
        )

        col1, col2 = st.columns(2)

        # -------------------------------------------------
        # BAR CHART
        # -------------------------------------------------

        with col1:

            fig = px.bar(
                category_data,
                x="category",
                y="amount",
                title="💰 Category Spending"
            )

            fig.update_layout(
                height=350,
                margin=dict(
                    t=55,
                    b=10,
                    l=10,
                    r=10
                ),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(
                    color="white"
                )
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        # -------------------------------------------------
        # DONUT CHART
        # -------------------------------------------------

        with col2:

            fig = px.pie(
                category_data,
                names="category",
                values="amount",
                hole=0.45,
                title="🍕 Spending Distribution"
            )

            fig.update_layout(
                height=350,
                margin=dict(
                    t=55,
                    b=10,
                    l=10,
                    r=10
                ),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(
                    color="white"
                )
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        # -------------------------------------------------
        # DAILY TREND
        # -------------------------------------------------

        daily_data = (
            df.groupby(
                "date"
            )["amount"]
            .sum()
            .reset_index()
        )

        fig = px.line(
            daily_data,
            x="date",
            y="amount",
            markers=True,
            title="📅 Spending Trend"
        )

        fig.update_layout(
            height=350,
            margin=dict(
                t=55,
                b=10,
                l=10,
                r=10
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(
                color="white"
            ),
            xaxis_title="Date",
            yaxis_title=f"Amount ({currency()})"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        # -------------------------------------------------
        # INSIGHTS
        # -------------------------------------------------

        st.subheader(
            "💡 Spending Insights"
        )

        highest_category = category_data.iloc[0]

        average_expense = (
            df["amount"].mean()
        )

        total_transactions = len(df)

        c1, c2, c3 = st.columns(3)

        with c1:

            st.metric(
                "🏆 Highest Category",
                highest_category["category"]
            )

        with c2:

            st.metric(
                "💸 Category Spending",
                money(
                    highest_category["amount"]
                )
            )

        with c3:

            st.metric(
                "📊 Average Expense",
                money(
                    average_expense
                )
            )


# =========================================================
# BUDGET
# =========================================================

elif st.session_state.page == "🎯 Budget":

    st.subheader(
        "🎯 Budget Manager"
    )

    limit = float(
        st.session_state.settings[
            "daily_limit"
        ]
    )

    spent = today_total()

    remaining = (
        limit - spent
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "🎯 Daily Limit",
            money(limit)
        )

    with col2:

        st.metric(
            "💸 Spent Today",
            money(spent)
        )

    with col3:

        if remaining >= 0:

            st.metric(
                "💰 Remaining",
                money(remaining)
            )

        else:

            st.metric(
                "🚨 Over Budget",
                money(abs(remaining))
            )

    st.write("")

    if limit > 0:

        progress = min(
            spent / limit,
            1.0
        )

        st.progress(progress)

    st.write("")

    if remaining < 0:

        st.markdown(
            f"""
            <div class="danger-box">
                🚨 You exceeded today's budget by
                <b>{money(abs(remaining))}</b>.
            </div>
            """,
            unsafe_allow_html=True
        )

    elif remaining <= limit * 0.2:

        st.markdown(
            f"""
            <div class="warning-box">
                ⚠️ You are close to your daily limit.<br>
                Remaining:
                <b>{money(remaining)}</b>
            </div>
            """,
            unsafe_allow_html=True
        )

    else:

        st.markdown(
            f"""
            <div class="success-box">
                🟢 You are within your daily budget.<br>
                Remaining:
                <b>{money(remaining)}</b>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.divider()

    st.subheader(
        "💡 Budget Tips"
    )

    if remaining < 0:

        st.write(
            "🔴 Your spending is above today's limit. "
            "Review your recent transactions."
        )

    elif remaining <= limit * 0.2:

        st.write(
            "🟡 You have less than 20% of your "
            "daily budget remaining."
        )

    else:

        st.write(
            "🟢 Good job! Your spending is currently "
            "within your daily budget."
        )


# =========================================================
# SETTINGS
# =========================================================

elif st.session_state.page == "⚙️ Settings":

    st.subheader(
        "⚙️ Settings"
    )

    settings = st.session_state.settings

    # -----------------------------------------------------
    # BUDGET SETTINGS
    # -----------------------------------------------------

    st.markdown(
        "### 🎯 Budget Settings"
    )

    with st.form("settings_form"):

        new_limit = st.number_input(
            "Daily Expense Limit",
            min_value=0.0,
            value=float(
                settings.get(
                    "daily_limit",
                    1000
                )
            ),
            step=100.0
        )

        currency_options = [
            "₹",
            "$",
            "€",
            "£",
            "¥"
        ]

        current_currency = settings.get(
            "currency",
            "₹"
        )

        currency_index = (
            currency_options.index(
                current_currency
            )
            if current_currency
            in currency_options
            else 0
        )

        new_currency = st.selectbox(
            "Currency",
            currency_options,
            index=currency_index
        )

        new_warning = st.slider(
            "Alert when spending reaches",
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

        save_settings_button = (
            st.form_submit_button(
                "💾 Save Settings",
                use_container_width=True
            )
        )

        if save_settings_button:

            new_settings = {

                "daily_limit":
                    float(new_limit),

                "currency":
                    new_currency,

                "warning_percentage":
                    int(new_warning)
            }

            st.session_state.settings = (
                new_settings
            )

            save_settings(
                new_settings
            )

            st.success(
                "✅ Settings saved successfully!"
            )

            st.rerun()

    # -----------------------------------------------------
    # EXPORT
    # -----------------------------------------------------

    st.divider()

    st.subheader(
        "📤 Export Data"
    )

    df = create_dataframe()

    if not df.empty:

        export_df = df.copy()

        export_df["date"] = (
            export_df["date"]
            .dt.strftime(
                "%Y-%m-%d"
            )
        )

        csv_data = export_df.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "📥 Download CSV",
            data=csv_data,
            file_name="expenses.csv",
            mime="text/csv",
            use_container_width=True
        )

    else:

        st.info(
            "No expenses available for export."
        )

    # -----------------------------------------------------
    # JSON BACKUP
    # -----------------------------------------------------

    st.subheader(
        "💾 JSON Backup"
    )

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

    # -----------------------------------------------------
    # RESTORE
    # -----------------------------------------------------

    st.subheader(
        "📥 Restore Backup"
    )

    uploaded_file = st.file_uploader(
        "Upload JSON backup",
        type=["json"]
    )

    if uploaded_file is not None:

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

                st.rerun()

            else:

                st.error(
                    "Invalid JSON backup format."
                )

        except json.JSONDecodeError:

            st.error(
                "The uploaded file is not valid JSON."
            )

    # -----------------------------------------------------
    # DANGER ZONE
    # -----------------------------------------------------

    st.divider()

    st.subheader(
        "⚠️ Danger Zone"
    )

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


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "💰 Smart Expense Tracker • "
    "Python + Streamlit + JSON + Plotly"
)
