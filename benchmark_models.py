import json
import os

from transformers import pipeline

if __name__ == "__main__":
    models = [
        "mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis",
        "ProsusAI/finbert",
        "yiyanghkust/finbert-tone",
    ]

    folder = os.path.join("data", "benchmark")
    os.makedirs(folder, exist_ok=True)

    with open(os.path.join("data", "random_headlines.json"), mode="r") as f:
        data = json.load(f)

    headlines = [item["headline"] for item in data]
    total_headlines = len(headlines)
    labels = [item["sentiment"] for item in data]

    for model_path in models:
        nlp = pipeline("sentiment-analysis", model=model_path, tokenizer=model_path)
        results = nlp(headlines)

        correct = 0
        with open(
            os.path.join(folder, f"{model_path.replace('/', '_')}.log"), mode="w"
        ) as f:
            print(f"Model: {model_path}\n", file=f)

            for headline, label, result in zip(headlines, labels, results):
                if label.lower() == result["label"].lower():
                    correct += 1

                else:
                    print(f"{headline}", file=f)
                    print(f"\tExpected: {label}\tPredicted: {result['label']}", file=f)
                    print(f"\t\t{result['score']}", file=f)

            print("\nAccuracy:", correct / total_headlines, file=f)
