
import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# =====================================================
# CONFIGURATION
# =====================================================

try:
    API_KEY = st.secrets["NEWS_API_KEY"]
except Exception:
    st.error(
        "NEWS_API_KEY not found. Please configure .streamlit/secrets.toml"
    )
    st.stop()

TOP_HEADLINES_URL = "https://newsapi.org/v2/top-headlines"
EVERYTHING_URL = "https://newsapi.org/v2/everything"

st.set_page_config(
    page_title="Advanced News Dashboard",
    page_icon="📰",
    layout="wide"
)

# =====================================================
# CUSTOM CSS
# =====================================================

st.markdown("""
<style>

.main {
    padding-top: 1rem;
}

.news-card {
    border: 1px solid #ddd;
    border-radius: 12px;
    padding: 15px;
    margin-bottom: 15px;
}

.metric-container {
    padding: 10px;
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)

# =====================================================
# SIDEBAR
# =====================================================

st.sidebar.title("📰 News Filters")

country_options = {
    "India": "in",
    "United States": "us",
    "United Kingdom": "gb",
    "Australia": "au",
    "Canada": "ca",
    "Germany": "de",
    "France": "fr",
    "Japan": "jp",
    "Italy": "it",
    "New Zealand": "nz"
}

selected_country = st.sidebar.selectbox(
    "🌍 Select Country",
    list(country_options.keys())
)

selected_category = st.sidebar.selectbox(
    "🏷 Select Topic",
    [
        "general",
        "business",
        "entertainment",
        "health",
        "science",
        "sports",
        "technology"
    ]
)

keyword = st.sidebar.text_input(
    "🔎 Search Keywords",
    placeholder="AI, Tesla, Cricket..."
)

num_articles = st.sidebar.slider(
    "📰 Number of Articles",
    min_value=5,
    max_value=100,
    value=20,
    step=5
)

# =====================================================
# FETCH NEWS
# =====================================================

@st.cache_data(ttl=300)
def fetch_news(country, category, query, page_size):

    try:

        # Use Everything API when keyword search exists
        if query.strip():

            params = {
                "apiKey": API_KEY,
                "q": query,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": page_size
            }

            response = requests.get(
                EVERYTHING_URL,
                params=params,
                timeout=15
            )

        else:

            params = {
                "apiKey": API_KEY,
                "country": country,
                "category": category,
                "pageSize": page_size
            }

            response = requests.get(
                TOP_HEADLINES_URL,
                params=params,
                timeout=15
            )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching news: {e}")
        return None


# =====================================================
# APP HEADER
# =====================================================

st.title("📰 Advanced News Dashboard")

st.markdown("""
Browse the latest headlines from around the world.

Use the filters in the sidebar to narrow results by:
- Country
- Topic
- Keywords
- Number of Articles
""")

# =====================================================
# FETCH DATA
# =====================================================

with st.spinner("Fetching latest news..."):

    news_data = fetch_news(
        country_options[selected_country],
        selected_category,
        keyword,
        num_articles
    )

# =====================================================
# DISPLAY RESULTS
# =====================================================

if news_data and news_data.get("status") == "ok":

    articles = news_data.get("articles", [])

    if len(articles) == 0:
        st.warning("No news articles found.")
        st.stop()

    # =================================================
    # DATAFRAME
    # =================================================

    records = []

    for article in articles:

        records.append({
            "Title": article.get("title"),
            "Source": article.get("source", {}).get("name"),
            "Author": article.get("author"),
            "Published": article.get("publishedAt"),
            "URL": article.get("url")
        })

    df = pd.DataFrame(records)

    # =================================================
    # METRICS
    # =================================================

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Articles",
            len(df)
        )

    with col2:
        st.metric(
            "Sources",
            df["Source"].nunique()
        )

    with col3:
        st.metric(
            "Country",
            selected_country
        )

    st.divider()

    # =================================================
    # CSV DOWNLOAD
    # =================================================

    csv = df.to_csv(index=False)

    st.download_button(
        label="📥 Download News as CSV",
        data=csv,
        file_name="news_articles.csv",
        mime="text/csv"
    )

    # =================================================
    # DATA TABLE
    # =================================================

    with st.expander("📊 News Dataset"):

        st.dataframe(
            df,
            use_container_width=True
        )

    # =================================================
    # SOURCE ANALYTICS
    # =================================================

    st.subheader("📈 Top News Sources")

    source_counts = (
        df["Source"]
        .value_counts()
        .head(10)
        .reset_index()
    )

    source_counts.columns = [
        "Source",
        "Articles"
    ]

    fig = px.bar(
        source_counts,
        x="Source",
        y="Articles",
        title="Top 10 News Sources"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.divider()

    # =================================================
    # NEWS ARTICLES
    # =================================================

    st.subheader("📰 Latest Headlines")

    for article in articles:

        title = article.get(
            "title",
            "No Title Available"
        )

        description = article.get(
            "description",
            "No Description Available"
        )

        image = article.get(
            "urlToImage"
        )

        source = article.get(
            "source",
            {}
        ).get(
            "name",
            "Unknown"
        )

        url = article.get(
            "url"
        )

        published = article.get(
            "publishedAt",
            ""
        )

        col1, col2 = st.columns(
            [1, 3]
        )

        with col1:

            if image:
                st.image(
                    image,
                    use_container_width=True
                )

        with col2:

            st.subheader(title)

            st.caption(
                f"📰 Source: {source} | 📅 Published: {published}"
            )

            st.write(description)

            if url:
                st.link_button(
                    "Read Full Article",
                    url
                )

        st.divider()

else:

    st.error(
        "Unable to fetch news. Check your API key or API limits."
    )
