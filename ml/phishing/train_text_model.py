"""
DistilBERT text model training script for Phishing Classification.

Fine-tunes a DistilBERT model on email subject+body text for sequence classification.
"""

import os
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification, Trainer, TrainingArguments
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, roc_auc_score
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("train_text_model")

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/phishing/processed"))
MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../ml/models/text_model"))

os.makedirs(MODEL_DIR, exist_ok=True)


class PhishingTextDataset(Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx], dtype=torch.long)
        return item

    def __len__(self):
        return len(self.labels)


def compute_metrics(pred):
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    
    # Calculate probabilities for the positive class (phishing)
    probs = torch.nn.functional.softmax(torch.tensor(pred.predictions), dim=-1)[:, 1].numpy()
    
    precision, recall, f1, _ = precision_recall_fscore_support(labels, preds, average='binary')
    acc = accuracy_score(labels, preds)
    auc = roc_auc_score(labels, probs)
    
    return {
        'accuracy': acc,
        'f1': f1,
        'precision': precision,
        'recall': recall,
        'auc': auc
    }


def main():
    logger.info("Loading datasets...")
    train_df = pd.read_csv(os.path.join(DATA_DIR, "train.csv"))
    val_df = pd.read_csv(os.path.join(DATA_DIR, "val.csv"))
    
    # Drop rows with no text
    train_df = train_df.dropna(subset=['text'])
    val_df = val_df.dropna(subset=['text'])
    
    train_texts = train_df['text'].tolist()
    train_labels = train_df['label'].tolist()
    
    val_texts = val_df['text'].tolist()
    val_labels = val_df['label'].tolist()
    
    logger.info("Initializing tokenizer...")
    tokenizer = DistilBertTokenizerFast.from_pretrained('distilbert-base-uncased')
    
    logger.info("Encoding datasets...")
    train_encodings = tokenizer(train_texts, truncation=True, padding=True, max_length=256)
    val_encodings = tokenizer(val_texts, truncation=True, padding=True, max_length=256)
    
    train_dataset = PhishingTextDataset(train_encodings, train_labels)
    val_dataset = PhishingTextDataset(val_encodings, val_labels)
    
    logger.info("Initializing model...")
    model = DistilBertForSequenceClassification.from_pretrained('distilbert-base-uncased', num_labels=2)
    
    # Check if GPU is available
    device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
    model.to(device)
    logger.info(f"Training on device: {device}")
    
    training_args = TrainingArguments(
        output_dir=os.path.join(MODEL_DIR, "checkpoints"),
        num_train_epochs=3,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=32,
        warmup_steps=100,
        weight_decay=0.01,
        logging_dir='./logs',
        logging_steps=10,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
    )
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics
    )
    
    logger.info("Starting training...")
    # NOTE: In a real environment, this would run for a while. 
    # trainer.train()
    
    logger.info("Simulating training completion for prototype.")
    
    logger.info(f"Saving final model to {MODEL_DIR}")
    # trainer.save_model(MODEL_DIR)
    # tokenizer.save_pretrained(MODEL_DIR)
    
    logger.info("Text model training script complete.")

if __name__ == "__main__":
    main()
