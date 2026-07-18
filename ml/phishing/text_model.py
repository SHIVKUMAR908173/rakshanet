import torch
import torch.nn as nn
from transformers import AutoModel
import torch.optim as optim
from torch.utils.data import DataLoader
from sklearn.metrics import precision_recall_fscore_support
 
class PhishingTextClassifier(nn.Module):
    def __init__(
        self,
        base_model_name="distilbert-base-multilingual-cased",
        hidden_dim: int = 768,
        dropout: float = 0.2,
    ):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(base_model_name)
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(hidden_dim, 1)
 
    def forward(self, input_ids, attention_mask):
        out = self.encoder(
            input_ids=input_ids, attention_mask=attention_mask
        )
        cls_embedding = out.last_hidden_state[:, 0, :]  # [CLS] token
        logits = self.classifier(self.dropout(cls_embedding))
        return logits.squeeze(-1)

def train_text_model(
    model,
    train_loader: DataLoader,
    val_loader: DataLoader,
    epochs: int = 4,
    lr: float = 2e-5,
    class_weight_pos: float = 3.0,
    device: str = "cuda",
):
    model.to(device)
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    total_steps = epochs * len(train_loader)
    scheduler = optim.lr_scheduler.LinearLR(
        optimizer, start_factor=1.0, end_factor=0.0,
        total_iters=total_steps,
    )
    pos_weight = torch.tensor(class_weight_pos, device=device)
    loss_fn = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
 
    best_val_f1 = 0.0
    for epoch in range(epochs):
        model.train()
        for batch in train_loader:
            optimizer.zero_grad()
            ids = batch["input_ids"].to(device)
            mask = batch["attention_mask"].to(device)
            logits = model(ids, mask)
            labels = batch["label"].float().to(device)
            loss = loss_fn(logits, labels)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(
                model.parameters(), max_norm=1.0
            )
            optimizer.step()
            scheduler.step()
 
        val_f1 = evaluate_text_model(model, val_loader, device)
        print(f"epoch {epoch + 1}/{epochs}  val_f1={val_f1:.4f}")
        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            torch.save(
                model.state_dict(),
                "checkpoints/phishing_text_best.pt",
            )
    return best_val_f1
 
 
def evaluate_text_model(model, loader: DataLoader, device: str) -> float:
    model.eval()
    preds, labels = [], []
    with torch.no_grad():
        for batch in loader:
            ids = batch["input_ids"].to(device)
            mask = batch["attention_mask"].to(device)
            logits = model(ids, mask)
            batch_preds = (torch.sigmoid(logits) > 0.5).long()
            preds.extend(batch_preds.cpu().tolist())
            labels.extend(batch["label"].tolist())
    _, _, f1, _ = precision_recall_fscore_support(
        labels, preds, average="binary", zero_division=0
    )
    return f1
