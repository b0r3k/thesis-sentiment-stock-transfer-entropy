import json
import os
import time

import eikon as ek
from dotenv import load_dotenv


def get_story(id: str, max_retries: int = 10) -> None:
    retries = 0
    while retries < max_retries:
        try:
            return ek.get_news_story(id, raw_output=True)

        except Exception as e:
            retries += 1
            print(f"Error getting story {id}: {e}")
            print(f"Retrying... ({retries}/{max_retries})")
            # Sleep for 3 seconds before retrying
            time.sleep(3)

    print(f"Failed to get story for {id} after {max_retries} retries")


def main() -> None:
    load_dotenv()
    ek.set_app_key(os.getenv("EIKON_APP_KEY"))

    out_dir = os.path.join("data", "stories")
    os.makedirs(out_dir, exist_ok=True)

    in_dir = os.path.join("data", "filtered_headlines")

    for i, file in enumerate(sorted(os.listdir(in_dir))):
        if not file.endswith(".json"):
            continue
        print(f"Processing file {i}: {file}")

        ric = file.split("_")[0]

        with open(os.path.join(in_dir, file)) as f:
            headlines = json.load(f)
            stories = []

            for j, headline in enumerate(headlines):
                if j % 100 == 0:
                    print(f"\tProcessing headline {j}/{len(headlines)}")

                id = headline["storyId"]
                stories.append(get_story(id))

            with open(
                os.path.join(out_dir, f"{ric}_stories.json"), "w", encoding="utf-8"
            ) as f:
                json.dump(stories, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
