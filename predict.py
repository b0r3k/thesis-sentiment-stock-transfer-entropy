import json
import os

from transformers import pipeline

if __name__ == "__main__":
    model_path = "ProsusAI/finbert"
    nlp = pipeline("sentiment-analysis", model=model_path, tokenizer=model_path)

    out_folder = os.path.join("data", "headlines_preds")
    os.makedirs(out_folder, exist_ok=True)

    in_folder = os.path.join("data", "headlines")

    for file in os.listdir(in_folder):
        if not file.endswith(".json"):
            continue

        print(f"Processing {file}")

        with open(os.path.join(in_folder, file), mode="r") as f:
            data = json.load(f)

        headlines = [sample["text"] for sample in data]

        print(f"\tNumber of headlines: {len(headlines)}")

        results = nlp(headlines)

        for original, result in zip(data, results):
            result.update(original)

        with open(os.path.join(out_folder, file), mode="w") as f:
            json.dump(results, f, indent=2)

        print(f"\tProcessed {file}")
        print(f"\tPredictions saved to {os.path.join(out_folder, file)}")
