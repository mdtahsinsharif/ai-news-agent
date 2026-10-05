
import streamlit as st
from collections import defaultdict

from database.news_queries import (
    get_todays_stories,
    get_story_articles,
)


category_colors = {
    "Technology": "#4F8BF9",
    "World": "#2E8B57",
    "Politics": "#8A5CF6",
    "Business": "#F39C12",
    "Science": "#00A6A6",
    "Sports": "#E74C3C",
    "Entertainment": "#E84393",
    "Health": "#27AE60",
    "Canada": "#D63031",
    "Other": "#7F8C8D",
}

st.set_page_config(
    page_title="AI News",
    layout="wide",
)

st.markdown(
    """
    <style>
    .category-header {
        padding: 12px 18px;
        margin-top: 30px;
        margin-bottom: 20px;
        border-left: 6px solid #4F8BF9;
        background-color: #F0F4F8;
        border-radius: 6px;
        font-size: 28px;
        font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("AI News")
st.caption("The last 24 hours of news, grouped into stories.")


# --------------------------------------------------
# Load stories from the last 24 hours
# --------------------------------------------------

stories = get_todays_stories()


if not stories:
    st.info("No news in the last 24 hours.")

else:

    # --------------------------------------------------
    # Group stories by category
    # --------------------------------------------------

    stories_by_category = defaultdict(list)

    for story in stories:
        category = (story["category"] or "Other").strip().lower()
        category = category.capitalize()
        stories_by_category[category].append(story)


    # --------------------------------------------------
    # Display a story
    # --------------------------------------------------


    def display_story(story):

        st.subheader(story["headline"])

        #st.write(
        #    story["summary"]
        #    or "Summary not available."
        #)

        #st.caption(
        #    f"{story['article_count']} sources"
        #)


        # ----------------------------------------------
        # Source articles
        # ----------------------------------------------

        articles = get_story_articles(
            story["id"]
        )

        for article in articles:

            
            if article["published_at"]:
                st.caption(
                    f"Published: {article['published_at']}"
                )
            
            st.markdown(
                f"[{article['title']}]({article['url']}) - "
                f"**{article['source']}**"
            )


            st.divider()


        # ----------------------------------------------
        # Separate stories
        # ----------------------------------------------

        st.divider()




    # --------------------------------------------------
    # Category display order
    # --------------------------------------------------

    category_order = [
        "Technology",
        "World",
        "Politics",
        "Business",
        "Science",
        "Sports",
        "Entertainment",
        "Health",
        "Canada",
        "Other",
    ]


    # --------------------------------------------------
    # Display categories
    # --------------------------------------------------

    displayed_categories = set()

    def display_category_header(category):

        color = category_colors.get(
            category,
            "#092022"
        )

        st.markdown(
            f"""
            <div style="
                padding: 12px 18px;
                margin-top: 30px;
                margin-bottom: 20px;
                border-left: 6px solid {color};
                background-color: {color};
                border-radius: 6px;
                font-size: 28px;
                font-weight: 700;
                color: black;
            ">
                {category}
            </div>
            """,
            unsafe_allow_html=True,
        )

    for category in category_order:

        if category not in stories_by_category:
            continue

        displayed_categories.add(category)

        display_category_header(category)

        # Only show top 5 stories
        top_stories = stories_by_category[category][:5]

        for story in top_stories:
            display_story(story)


    # --------------------------------------------------
    # Display any categories not in the predefined list
    # --------------------------------------------------

    for category, category_stories in stories_by_category.items():

        if category in displayed_categories:
            continue

        st.header(category)

        # Only show top 5 stories
        top_stories = category_stories[:5]

        for story in top_stories:
            display_story(story)
