import streamlit as st

st.set_page_config(page_title="Cornell Library – Welcome", layout="wide")

# ---------- CSS ----------
st.markdown(
    """
    <style>

    :root {
        font-size: 22px;
    }
    .block-container {
        padding-top: 3rem;
        padding-bottom: 3rem;
        max-width: 1100px;
    }
    body {
        background: radial-gradient(circle at 0% 0%, #f5f7ff 0, #eceff7 40%, #e5e9f5 80%);
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    .hero-badge {
        display: inline-block;
        padding: 6px 14px;
        border-radius: 999px;
        background: #ffe5e5;
        color: #b31b1b;
        font-weight: 600;
        font-size: 0.85rem;
        margin-bottom: 1rem;
    }
    .hero-title {
        font-size: 2.8rem;
        line-height: 1.1;
        font-weight: 800;
        color: #80838a;
        margin-bottom: 1rem;
    }
    .hero-title span {
        color: #b31b1b;
    }
    .hero-desc {
        font-size: 1.05rem;
        color: #d1d6e0;
        max-width: 32rem;
        margin-bottom: 1.8rem;
    }
    .hero-buttons {
        display: flex;
        flex-wrap: wrap;
        gap: 0.8rem;
        margin-bottom: 2.2rem;
    }
    .hero-btn-main, .hero-btn-ghost {
        border-radius: 999px;
        border: none;
        padding: 0.7rem 1.8rem;
        font-weight: 600;
        font-size: 0.95rem;
    }
    .hero-btn-main {
        background: #b31b1b;
        color: #ffffff;
        box-shadow: 0 12px 24px rgba(179, 27, 27, 0.35);
    }
    .hero-btn-ghost {
        background: #f9fafb;
        color: #111827;
        border: 1px solid #9ca3af;
    }
    .stats-row {
        display: flex;
        gap: 2rem;
    }
    .stat-item span:first-child {
        display: block;
        font-size: 2.0rem;
        font-weight: 700;
        color: #b31b1b;
    }
    .stat-item span:last-child {
        font-size: 0.6rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #6b7280;
    }
    .hero-card {
    background: #ffffff;
    border-radius: 20px;
    padding: 1.2rem;
    box-shadow: 0 18px 40px rgba(15, 23, 42, 0.18);
    }

    .hero-card-inner {
        border-radius: 18px;
        padding: 3rem 2.4rem;
        background: linear-gradient(140deg, #5d8df9, #6c63ff, #7041d9);
        color: #ffffff;
        font-size: 1.25rem;
        font-weight: 600;

        /* make it as tall as the text area */
        min-height: 360px;      /* increase/decrease until it visually matches */
        display: flex;
        align-items: center;    /* keeps the text vertically centered */
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- HERO LAYOUT ----------
left, right = st.columns([3, 4])

with left:
    st.markdown(
        '<div class="hero-badge">🚀 Smart Library Information System</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="hero-title">The Future of<br><span>Library Experience</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <p class="hero-desc">
        Experience seamless, autonomous study space discovery with
        AI-powered booking, real-time occupancy tracking, and digital
        navigation. No waiting, no guessing.
        </p>
        """,
        unsafe_allow_html=True,
    )

    # Buttons
    st.markdown('<div class="hero-buttons">', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Launch Dashboard →", key="view_dashboard", use_container_width=True):
            st.switch_page("pages/1_Availability.py")
    with col2:
        if st.button("Book A Room →", key="book_room", use_container_width=True):
            st.switch_page("pages/2_RoomReservation.py")
   
    st.markdown("</div>", unsafe_allow_html=True)

    # Stats row
    st.markdown('<div class="stats-row">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            '<div class="stat-item"><span>7</span><span>Libraries</span></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            '<div class="stat-item"><span>2,847</span><span>Total Seats</span></div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            '<div class="stat-item"><span>0</span><span>Available Now</span></div>',
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-card-inner">
                📊 Live Dashboard Preview
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
