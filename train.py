import pandas as pd
import torch
import torch.nn as nn
import json

data = pd.read_csv("build/dataset.csv", header=None)

print(data.shape)  # affiche le nombre de lignes et colonnes
print(data.head()) # affiche les 5 premières lignes

X = data.iloc[:, :9]  # toutes les lignes, colonnes 0 à 8
y = data.iloc[:, 9]   # toutes les lignes, colonne 9

X_tensor = torch.tensor(X.values, dtype=torch.float32)
y_tensor = torch.tensor(y.values, dtype=torch.float32)


class TicTacToeNet(nn.Module):
    def __init__(self):
        super(TicTacToeNet, self).__init__()
        self.fc1 = nn.Linear(9, 64)
        self.fc2 = nn.Linear(64, 64)
        self.fc3 = nn.Linear(64, 1)
        self.relu = nn.ReLU()

    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        x = torch.tanh(self.fc3(x))  # limite entre -1 et +1
        return x
    



model = TicTacToeNet()
criterion = nn.MSELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)


epochs = 100

for epoch in range(epochs):
    optimizer.zero_grad()
    output = model(X_tensor)
    loss = criterion(output.squeeze(), y_tensor)
    loss.backward()
    optimizer.step()
    
    if epoch % 10 == 0:
        print(f"Epoch {epoch}, Loss: {loss.item():.4f}")



torch.save(model.state_dict(), "model_weights.pth")
print("Poids sauvegardés !")


weights = {}
for name, param in model.state_dict().items():
    weights[name] = param.tolist()

with open("model_weights.json", "w") as f:
    json.dump(weights, f)

print("Poids exportés en JSON !")