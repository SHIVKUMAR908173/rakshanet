"""
Autoencoder training script for Network/OT Anomaly Detection.

Trains an unsupervised PyTorch Autoencoder. The model is trained on
predominantly normal (benign) traffic. At inference time, high reconstruction
error signals an anomaly.
"""

import os
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, roc_auc_score
import logging

from feature_engineering import process_anomaly_dataframe

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("train_autoencoder")

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/anomaly/processed"))
MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../ml/models/anomaly_model"))

os.makedirs(MODEL_DIR, exist_ok=True)

class NetworkAutoencoder(nn.Module):
    def __init__(self, input_dim):
        super(NetworkAutoencoder, self).__init__()
        
        # Encoder
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 16),
            nn.ReLU(True),
            nn.Dropout(0.1),
            nn.Linear(16, 8),
            nn.ReLU(True),
            nn.Linear(8, 4)
        )
        
        # Decoder
        self.decoder = nn.Sequential(
            nn.Linear(4, 8),
            nn.ReLU(True),
            nn.Dropout(0.1),
            nn.Linear(8, 16),
            nn.ReLU(True),
            nn.Linear(16, input_dim)
        )

    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded


def get_threshold(errors, percentile=95):
    """Calculate the anomaly threshold based on the error distribution of normal traffic."""
    return np.percentile(errors, percentile)


def main():
    logger.info("Loading datasets...")
    train_df = pd.read_csv(os.path.join(DATA_DIR, "train.csv"))
    val_df = pd.read_csv(os.path.join(DATA_DIR, "val.csv"))
    
    logger.info("Extracting features...")
    _, net_train = process_anomaly_dataframe(train_df)
    _, net_val = process_anomaly_dataframe(val_df)
    
    if len(net_train) == 0:
        logger.error("No network/OT records found in training data.")
        return
        
    features = [c for c in net_train.columns if c != "label"]
    
    # Autoencoders should be trained primarily on normal data to learn the "normal" manifold
    normal_train = net_train[net_train["label"] == 0]
    X_train_normal = normal_train[features].values
    
    X_val = net_val[features].values
    y_val_true = net_val["label"].values
    
    # Scale features
    logger.info("Scaling features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_normal)
    X_val_scaled = scaler.transform(X_val)
    
    # Convert to PyTorch tensors
    train_tensor = torch.FloatTensor(X_train_scaled)
    val_tensor = torch.FloatTensor(X_val_scaled)
    
    train_dataset = TensorDataset(train_tensor, train_tensor)
    train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
    
    # Initialize Model
    input_dim = X_train_scaled.shape[1]
    model = NetworkAutoencoder(input_dim)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.to(device)
    
    epochs = 20
    logger.info(f"Training Autoencoder on {device} for {epochs} epochs...")
    
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        for data in train_loader:
            inputs, _ = data
            inputs = inputs.to(device)
            
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, inputs)
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            
        if (epoch+1) % 5 == 0:
            logger.info(f"Epoch [{epoch+1}/{epochs}], Loss: {total_loss/len(train_loader):.4f}")
            
    # Evaluation and threshold finding
    logger.info("Evaluating and finding threshold...")
    model.eval()
    with torch.no_grad():
        # Get errors for the validation set
        val_inputs = val_tensor.to(device)
        val_outputs = model(val_inputs)
        # Mean Squared Error per sample
        mse = torch.mean((val_inputs - val_outputs)**2, dim=1).cpu().numpy()
        
    # Get errors specifically for the benign validation traffic to set threshold
    benign_val_errors = mse[y_val_true == 0]
    threshold = get_threshold(benign_val_errors, 95)
    logger.info(f"Calculated Anomaly Threshold (95th percentile of normal): {threshold:.4f}")
    
    # Predict anomalies
    preds = (mse > threshold).astype(int)
    
    precision, recall, f1, _ = precision_recall_fscore_support(y_val_true, preds, average='binary')
    acc = accuracy_score(y_val_true, preds)
    auc = roc_auc_score(y_val_true, mse)
    
    logger.info("--- Validation Metrics ---")
    logger.info(f"Accuracy:  {acc:.4f}")
    logger.info(f"Precision: {precision:.4f}")
    logger.info(f"Recall:    {recall:.4f}")
    logger.info(f"F1 Score:  {f1:.4f}")
    logger.info(f"AUC:       {auc:.4f}")
    
    # Save Model and Scaler
    model_path = os.path.join(MODEL_DIR, "autoencoder.pt")
    scaler_path = os.path.join(MODEL_DIR, "ae_scaler.pkl")
    
    logger.info(f"Saving model to {model_path}")
    torch.save(model.state_dict(), model_path)
    
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
        
    # Also save the threshold
    with open(os.path.join(MODEL_DIR, "ae_threshold.txt"), 'w') as f:
        f.write(str(threshold))
        
    logger.info("Autoencoder training complete.")

if __name__ == "__main__":
    main()
