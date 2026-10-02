import time

from google.genai import types
from pydantic import BaseModel

from ai.embeddings import client
from ai.text import clean_text
from database.repository import get_story_titles


# A yes/no judgement doesn't need a large model; lite is fast
# and has a higher free-tier quota.
MODEL = "gemini-3.5-flash-lite"

MAX_CALLS_PER_RUN = 150

# The free tier allows about 15 requests per minute.
MIN_SECONDS_BETWEEN_CALLS = 4.5
RATE_LIMIT_WAIT_SECONDS = 60


class SameStoryVerdict(BaseModel):

    same_story: bool


def describe_article(article):

    description = clean_text(
        article.get("description")
    )[:300]

    return f"{article['title']}\n{description}".strip()


def describe_story(story_id):

    titles = get_story_titles(story_id)

    return "\n".join(
        f"- {title}"
        for title in titles
    )


class SameStoryChecker:
    """
    Asks Gemini whether two pieces of coverage describe the
    same news story. Used for similarity scores in the gray
    zone where embeddings alone can't tell.
    """

    def __init__(self, max_calls=MAX_CALLS_PER_RUN):

        self.max_calls = max_calls
        self.calls = 0
        self.disabled = False
        self.last_call_at = 0.0

    def check(self, coverage_a, coverage_b):
        """
        Return True/False, or None when the model couldn't
        be asked (call budget spent, quota, API error).
        """

        if self.disabled or self.calls >= self.max_calls:
            return None

        self.calls += 1

        prompt = f"""
Do these two pieces of news coverage report on the same
news story?

Answer true if both report on the same specific event or
development, including follow-ups to it such as reactions,
investigations, new details, or analysis of that event.

Answer false if they only share a broad topic, place,
organisation, or person but report different events.

Coverage A:
{coverage_a}

Coverage B:
{coverage_b}
"""

        try:

            response = self._generate(prompt)

        except Exception as e:

            if "RESOURCE_EXHAUSTED" not in str(e):

                print(f"Same-story check failed: {str(e)[:120]}")

                return None

            if "PerDay" in str(e):

                print("Same-story daily quota exhausted.")

                self.disabled = True

                return None

            # Per-minute limit: wait it out and retry once.
            print(
                "Same-story rate limit hit, waiting "
                f"{RATE_LIMIT_WAIT_SECONDS}s..."
            )

            time.sleep(RATE_LIMIT_WAIT_SECONDS)

            try:

                response = self._generate(prompt)

            except Exception as e:

                print(f"Same-story check failed: {str(e)[:120]}")

                self.disabled = "RESOURCE_EXHAUSTED" in str(e)

                return None

        if response.parsed is None:
            return None

        return response.parsed.same_story

    def _generate(self, prompt):

        wait = (
            self.last_call_at
            + MIN_SECONDS_BETWEEN_CALLS
            - time.monotonic()
        )

        if wait > 0:
            time.sleep(wait)

        self.last_call_at = time.monotonic()

        return client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=SameStoryVerdict,
            ),
        )
