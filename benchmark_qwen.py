import asyncio
import json
import os
import re

import ollama

SYSTEM_PROMPT = """You are a financial sentiment analysis expert. Your task is to analyze a list (one per line) of news headlines and assess the financial tone of each headline. For each headline, perform the following:

1. Classify the sentiment as:
   - Positive
   - Negative
   - Neutral
Note that each headline was extracted in relation to a specific company and you should detect the implicit sentiment of such headline – e.g. if the headline talks about highlights in analyst blog, it is positive that the company was mentioned in such an article.

2. Provide a confidence of your classification as a 0-1 float.

Output your analysis as a JSON array where each entry is an object with the keys "headline", "sentiment", and "confidence". Ensure your output preserves the order of the input headlines.

Below is an example input and the expected output format:

Example Input:
  Microsoft in talks to acquire Activision Blizzard to expand its gaming division.
  Tesla reports a 20% drop in quarterly revenue amid supply chain disruptions.
  Apple posts steady growth in Q2, maintaining investor confidence.
  Goldman Sachs warns of an impending economic slowdown due to rising inflation.
  The Zacks Analyst Blog Highlights Novo Nordisk, Eli Lilly, Vertex Pharmaceuticals, Regeneron and GSK

Expected Output:
[
  {
    "headline": "The Zacks Analyst Blog Highlights Novo Nordisk, Eli Lilly, Vertex Pharmaceuticals, Regeneron and GSK.",
    "sentiment": "Positive",
    "confidence": 0.94
  },
  {
    "headline": "Microsoft in talks to acquire Activision Blizzard to expand its gaming division.",
    "sentiment": "Positive",
    "confidence": 0.92
  },
  {
    "headline": "Tesla reports a 20% drop in quarterly revenue amid supply chain disruptions.",
    "sentiment": "Negative",
    "confidence": 0.99
  },
  {
    "headline": "Apple posts steady growth in Q2, maintaining investor confidence.",
    "sentiment": "Neutral",
    "confidence": 0.6
  },
  {
    "headline": "Goldman Sachs warns of an impending economic slowdown due to rising inflation.",
    "sentiment": "Negative",
    "confidence": 0.95
  }
]

Instructions:
- Read each headline carefully.
- Identify key financial indicators and market sentiments.
- Base your sentiment classification on the tone and potential financial impact of the news.
- Process all of the headlines.

Please now process the list and provide your analysis.

INPUT:
"""

# Create a custom client with a specific host
client = ollama.AsyncClient(host="http://100.119.56.67:11434")


# Function to analyze a single headline
async def analyze_headline(headline):
    response = await client.generate(
        model="qwen3:8b",
        prompt=headline,
        options={
            "system": SYSTEM_PROMPT,
            "template": "{{ if .System }}<|im_start|>system\n{{ .System }}<|im_end|>\n{{ end }}{{ if .Prompt }}<|im_start|>user\n{{ .Prompt }}<|im_end|>\n{{ end }}<|im_start|>assistant\n",
        },
        stream=False,
    )

    # Parse response: <think> something </think> json
    match = re.search(r"<think>([\s\S]*?)<\/think>\s*([\s\S]+)", response["response"])
    if match:
        think = match.group(1).strip()
        try:
            obj = json.loads(match.group(2))
        except Exception as e:
            obj = {"error": f"Failed to parse JSON, {str(e)}", "raw": match.group(2)}

        # If obj is an array with one object, merge think into that object
        if isinstance(obj, list) and len(obj) == 1 and isinstance(obj[0], dict):
            obj = {**obj[0], "think": think}
        elif isinstance(obj, dict):
            obj["think"] = think

        return obj

    return {"error": "No <think> tag found", "raw": response["response"]}


# Process all headlines
async def ollama_predict():
    # Load headlines from JSON file
    with open(os.path.join("data", "random_headlines.json"), "r") as file:
        headlines_data = json.load(file)

    results = []
    for item in headlines_data:
        result = await analyze_headline(item["headline"])
        results.append(result)
        print(result)

    with open(os.path.join("data", "benchmark", "qwen.json"), "w") as file:
        json.dump(results, file, indent=2)


def evaluate_print():
    model_path = "qwen3:8b"

    with open(os.path.join("data", "random_headlines.json"), mode="r") as f:
        data = json.load(f)

    headlines = [item["headline"] for item in data]
    total_headlines = len(headlines)
    labels = [item["sentiment"] for item in data]

    with open(os.path.join("data", "benchmark", "qwen.json")) as f:
        results = json.load(f)

    correct = 0
    with open(
        os.path.join("data", "benchmark", f"{model_path.replace(':', '_')}.log"),
        mode="w",
    ) as f:
        print(f"Model: {model_path} through Ollama\n", file=f)

        for headline, label, result in zip(headlines, labels, results):
            if label.lower() == result["sentiment"].lower():
                correct += 1

            else:
                print(f"{headline}", file=f)
                print(f"\tExpected: {label}\tPredicted: {result['sentiment']}", file=f)
                print(f"\t\t{result['confidence']}", file=f)

        print("\nAccuracy:", correct / total_headlines, file=f)


if __name__ == "__main__":
    asyncio.run(ollama_predict())
    evaluate_print()
