import yaml

from ingestion.rss import fetch_feed


with open("config/sources.yaml") as f:
    config = yaml.safe_load(f)


all_articles = []


for source in config["sources"]:

    print(
        f"\nFetching {source['name']}..."
    )

    articles = fetch_feed(
        source["name"],
        source["url"]
    )

    print(
        f"Retrieved {len(articles)} articles"
    )

    all_articles.extend(articles)


print("\n====================")
print("TOTAL ARTICLES:", len(all_articles))
print("====================")