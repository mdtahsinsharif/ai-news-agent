
import yaml

from ingestion.rss import fetch_feed


def load_sources():

    with open(
        "config/sources.yaml",
        "r",
    ) as file:

        config = yaml.safe_load(file)

    return config["sources"]


def fetch_all_sources():

    sources = load_sources()

    all_articles = []

    for source in sources:

        print(
            f"\nFetching {source['name']}..."
        )

        articles = fetch_feed(
            source_name=source["name"],
            url=source["url"],
            category=source["category"],
        )

        print(
            f"Found {len(articles)} articles"
        )

        all_articles.extend(
            articles
        )

    return all_articles
