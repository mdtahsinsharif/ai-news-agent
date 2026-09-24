from database.news_queries import get_todays_stories

stories = get_todays_stories()

for story in stories:

    print(
        story["headline"]
    )

    print(
        story["summary"]
    )

    print(
        "Articles:",
        story["article_count"]
    )

    print()