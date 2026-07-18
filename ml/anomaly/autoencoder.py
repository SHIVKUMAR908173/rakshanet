import torch
import torch.nn as nn
 
NETWORK_FEATURES = [
    "volume_bytes_norm", "protocol_entropy", "destination_entropy",
    "session_duration_norm", "new_destination_country_flag",
    "ot_command_freq_dev",
]
 
class TrafficAutoencoder(nn.Module):
    def __init__(
        self, input_dim: int = len(NETWORK_FEATURES), latent_dim: int = 3
    ):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 16), nn.ReLU(),
            nn.Linear(16, 8), nn.ReLU(),
            nn.Linear(8, latent_dim),
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 8), nn.ReLU(),
            nn.Linear(8, 16), nn.ReLU(),
            nn.Linear(16, input_dim),
        )
 
    def forward(self, x):
        z = self.encoder(x)
        return self.decoder(z)
 
 
def train_autoencoder(
    model,
    train_loader,
    epochs: int = 30,
    lr: float = 1e-3,
    device: str = "cuda",
    patience: int = 5,
):
    model.to(device)
    optimizer = torch.optim.Adam(
        model.parameters(), lr=lr, weight_decay=1e-5
    )
    loss_fn = nn.MSELoss()
    best_loss, stale = float("inf"), 0
 
    for epoch in range(epochs):
        model.train()
        epoch_loss = 0.0
        for batch in train_loader:
            x = batch.to(device)
            optimizer.zero_grad()
            recon = model(x)
            loss = loss_fn(recon, x)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item() * x.size(0)
        epoch_loss /= len(train_loader.dataset)
        print(f"epoch {epoch + 1}/{epochs}  recon_loss={epoch_loss:.5f}")
 
        if epoch_loss < best_loss - 1e-5:
            best_loss, stale = epoch_loss, 0
            torch.save(
                model.state_dict(),
                "checkpoints/traffic_autoencoder_best.pt",
            )
        else:
            stale += 1
            if stale >= patience:
                print("early stopping")
                break
    return best_loss
 
 
def reconstruction_error(model, x: torch.Tensor) -> torch.Tensor:
    model.eval()
    with torch.no_grad():
        recon = model(x)
        return ((recon - x) ** 2).mean(dim=1)
