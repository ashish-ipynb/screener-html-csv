import streamlit as st
from parser import parse_html

# ======================================================
# Page Configuration
# ======================================================

st.set_page_config(
    page_title="Screener HTML to CSV Converter",
    page_icon="📈",
    layout="wide"
)

# ======================================================
# Title
# ======================================================

st.title("📈 Screener HTML to CSV Converter")

st.markdown("""
Upload a manually downloaded **Screener Latest Quarterly Results** HTML file.

The application will:

- ✅ Extract financial data
- ✅ Convert it into a structured table
- ✅ Generate a downloadable CSV
""")

st.divider()

# ======================================================
# File Upload
# ======================================================

uploaded_file = st.file_uploader(
    "Choose an HTML file",
    type=["html", "htm"]
)

# ======================================================
# Parse File
# ======================================================

if uploaded_file is not None:

    try:

        with st.spinner("Parsing HTML..."):

            df = parse_html(uploaded_file)

        st.success("HTML parsed successfully!")

        # =============================================
        # Statistics
        # =============================================

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Companies",
                df["Company Name"].nunique()
            )

        with col2:
            st.metric(
                "Records",
                len(df)
            )

        with col3:
            st.metric(
                "Metrics / Company",
                len(df) // df["Company Name"].nunique()
            )

        st.divider()

        # =============================================
        # Preview
        # =============================================

        st.subheader("Preview")

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        # =============================================
        # Download Button
        # =============================================

        csv = df.to_csv(
            index=False
        ).encode("utf-8-sig")

        st.download_button(
            label="⬇ Download CSV",
            data=csv,
            file_name="Latest_Quarterly_Results.csv",
            mime="text/csv"
        )

    except Exception as e:

        st.error(str(e))

else:

    st.info("Upload an HTML file to begin.")
    
st.divider()

st.markdown(
    """
    <div style="text-align:center; color:gray; font-size:14px;">
        Made with ❤️ by
        <a href="https://github.com/ashish-ipynb" target="_blank">
            <b>Ashish Kumar</b>
        </a><br>
        <span style="font-size:13px;">
            M.Sc. Bioinformatics • Open Source Project
        </span>
    </div>
    """,
    unsafe_allow_html=True
)
st.caption(
    "Convert a manually downloaded Screener 'Latest Quarterly Results' HTML page into a structured CSV."
)

with st.expander("ℹ️ About this application"):
    st.write(
        """
        This application extracts financial data from a manually downloaded
        Screener **Latest Quarterly Results** HTML page and converts it into
        a structured CSV for further analysis.
        """
    )
    
st.markdown(
    "[🌐 View Source Code](https://github.com/ashish-ipynb/screener-html-csv)"
)