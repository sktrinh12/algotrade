from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
device = "cuda:0" if torch.cuda.is_available() else "cpu"

tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert").to(device)
labels = ["positive", "negative", "neutral"]

def estimate_sentiment(news):
    if news:
        tokens = tokenizer(news, return_tensors="pt", padding=True).to(device)

        result = model(tokens["input_ids"], attention_mask=tokens["attention_mask"])[
            "logits"
        ]
        result = torch.nn.functional.softmax(torch.sum(result, 0), dim=-1)
        probability = result[torch.argmax(result)]
        sentiment = labels[torch.argmax(result)]
        return probability, sentiment
    else:
        return 0, labels[-1]


if __name__ == "__main__":
    sample_news_text = [
    "Apple Inc. (AAPL) reported strong quarterly earnings, beating Wall Street expectations.",
    "The tech giant saw a surge in iPhone sales and continued growth in its services business.",
    "Analysts remain bullish on Apple's long-term prospects, citing the company's ecosystem and innovation pipeline.",
    "Apple's CEO Tim Cook expressed optimism about the company's future, highlighting the potential of new products and services.",
    "Despite global supply chain challenges, Apple managed to deliver impressive results, showcasing its resilience and adaptability."
]
    tensor, sentiment = estimate_sentiment(sample_news_text)
    # tensor, sentiment = estimate_sentiment(['markets responded negatively to the news!','traders were displeased!'])
    print(tensor, sentiment)
    print(f'cuda available: {torch.cuda.is_available()}')
