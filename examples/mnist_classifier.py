#!/usr/bin/env python
"""Variational Quantum Classifier for MNIST binary classification.

This example demonstrates:
- Loading MNIST data and filtering for binary classification
- PCA dimensionality reduction for angle encoding
- HEA ansatz as quantum classifier
- PyTorch integration for training

Requirements:
    pip install qpandalite[pytorch] torchvision scikit-learn

Usage:
    python mnist_classifier.py --n-samples 500 --epochs 20
"""

import argparse
import numpy as np

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset
    from torchvision import datasets, transforms
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install qpandalite[pytorch] torchvision scikit-learn")
    raise

from qpandalite.circuit_builder import Circuit, Parameters
from qpandalite.algorithmics.ansatz import hea
from qpandalite.simulator import OriginIR_Simulator
from qpandalite.pytorch import batch_execute_with_params


# ============================================================================
# Data Loading and Preprocessing
# ============================================================================

def load_mnist_binary(n_samples=1000, n_features=8, digits=(0, 1)):
    """Load MNIST, filter for two digits, reduce dimensionality with PCA.

    Args:
        n_samples: Maximum samples per class
        n_features: Number of PCA components (will be encoded as rotation angles)
        digits: Tuple of two digit classes for binary classification

    Returns:
        X_train, X_test, y_train, y_test: Training and test data
    """
    print(f"Loading MNIST data (digits {digits[0]} vs {digits[1]})...")

    # Load MNIST
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Lambda(lambda x: x.view(-1))  # Flatten to 784
    ])

    train_dataset = datasets.MNIST('./data', train=True, download=True, transform=transform)
    test_dataset = datasets.MNIST('./data', train=False, download=True, transform=transform)

    # Filter for two digits
    def filter_digits(dataset, digits, max_per_class):
        X, y = [], []
        counts = {d: 0 for d in digits}
        for img, label in dataset:
            if label in digits and counts[label] < max_per_class:
                X.append(img.numpy())
                y.append(digits.index(label))  # Map to 0 or 1
                counts[label] += 1
            if all(c >= max_per_class for c in counts.values()):
                break
        return np.array(X), np.array(y)

    X_train, y_train = filter_digits(train_dataset, digits, n_samples)
    X_test, y_test = filter_digits(test_dataset, digits, n_samples // 5)

    print(f"  Training samples: {len(X_train)}")
    print(f"  Test samples: {len(X_test)}")

    # Standardize and apply PCA
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    pca = PCA(n_components=n_features)
    X_train_pca = pca.fit_transform(X_train_scaled)
    X_test_pca = pca.transform(X_test_scaled)

    # Scale to [0, π] for angle encoding
    X_train_encoded = (X_train_pca - X_train_pca.min()) / (X_train_pca.max() - X_train_pca.min()) * np.pi
    X_test_encoded = (X_test_pca - X_train_pca.min()) / (X_train_pca.max() - X_train_pca.min()) * np.pi

    print(f"  Explained variance ratio: {pca.explained_variance_ratio_.sum():.2%}")

    return X_train_encoded, X_test_encoded, y_train, y_test


# ============================================================================
# Variational Quantum Classifier
# ============================================================================

class VQC(nn.Module):
    """Variational Quantum Classifier using HEA ansatz.

    Architecture:
        1. Angle encoding: Encode n_features using Ry rotations on n_qubits
        2. HEA ansatz: Parameterized quantum circuit with entangling layers
        3. Measurement: Probability of |0⟩ on first qubit as output
    """

    def __init__(self, n_qubits, depth=2):
        super().__init__()
        self.n_qubits = n_qubits
        self.depth = depth
        self.n_params = 2 * n_qubits * depth

        # Learnable parameters for HEA
        self.params = nn.Parameter(torch.randn(self.n_params) * 0.1)

        # Simulated expectation values (for demo; real QML would compute these)
        self.sim = OriginIR_Simulator(backend_type='statevector')

    def build_circuit(self, x, params):
        """Build the VQC circuit for input x and parameters."""
        c = Circuit(self.n_qubits)

        # Angle encoding: Ry rotations based on input features
        for i, xi in enumerate(x):
            if i < self.n_qubits:
                c.ry(i, float(xi))

        # HEA ansatz
        hea_circuit = hea(self.n_qubits, depth=self.depth, params=params.detach().numpy())
        c.add_circuit(hea_circuit)

        return c

    def forward(self, x):
        """Forward pass through the quantum classifier."""
        batch_size = x.shape[0]
        outputs = []

        for i in range(batch_size):
            circuit = self.build_circuit(x[i], self.params)
            probs = self.sim.simulate_pmeasure(circuit.originir)

            # Use probability of states where first qubit is 0 as output
            prob_0 = sum(probs[j] for j in range(len(probs) // 2))
            outputs.append(prob_0)

        return torch.tensor(outputs, requires_grad=True).unsqueeze(1)


# ============================================================================
# Hybrid Model (Classical + Quantum)
# ============================================================================

class HybridClassifier(nn.Module):
    """Hybrid classical-quantum classifier.

    For larger feature sets, use classical preprocessing before quantum layer.
    """

    def __init__(self, input_dim, n_qubits, depth=2):
        super().__init__()

        # Classical preprocessing
        self.pre = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, n_qubits),
            nn.Tanh()  # Scale to [-1, 1]
        )

        # Quantum layer
        self.vqc = VQC(n_qubits, depth)

        # Classical postprocessing
        self.post = nn.Sequential(
            nn.Linear(1, 2)  # Binary classification
        )

    def forward(self, x):
        x = self.pre(x) * np.pi  # Scale to [-π, π] for angle encoding
        x = self.vqc(x)
        x = self.post(x)
        return x


# ============================================================================
# Training Loop
# ============================================================================

def train_model(model, X_train, y_train, epochs=20, lr=0.01, batch_size=32):
    """Train the model."""
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()

    dataset = TensorDataset(
        torch.FloatTensor(X_train),
        torch.LongTensor(y_train)
    )
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    print("\nTraining...")
    print("-" * 50)

    for epoch in range(epochs):
        model.train()
        total_loss = 0
        correct = 0
        total = 0

        for X_batch, y_batch in loader:
            optimizer.zero_grad()
            output = model(X_batch)
            loss = criterion(output, y_batch)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            pred = output.argmax(dim=1)
            correct += (pred == y_batch).sum().item()
            total += len(y_batch)

        acc = correct / total
        print(f"Epoch {epoch+1:3d}/{epochs} | Loss: {total_loss:.4f} | Acc: {acc:.2%}")

    return model


def evaluate_model(model, X_test, y_test):
    """Evaluate the model on test data."""
    model.eval()
    with torch.no_grad():
        X = torch.FloatTensor(X_test)
        y = torch.LongTensor(y_test)
        output = model(X)
        pred = output.argmax(dim=1)
        acc = (pred == y).float().mean().item()

    print(f"\nTest accuracy: {acc:.2%}")
    return acc


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='MNIST VQC Classifier')
    parser.add_argument('--n-samples', type=int, default=500, help='Samples per class')
    parser.add_argument('--n-features', type=int, default=8, help='PCA components (qubits)')
    parser.add_argument('--depth', type=int, default=2, help='HEA depth')
    parser.add_argument('--epochs', type=int, default=20, help='Training epochs')
    parser.add_argument('--lr', type=float, default=0.01, help='Learning rate')
    args = parser.parse_args()

    print("=" * 60)
    print("Variational Quantum Classifier for MNIST")
    print("=" * 60)
    print(f"Configuration: {args.n_features} qubits, HEA depth={args.depth}")
    print(f"Parameters: {2 * args.n_features * args.depth}")

    # Load data
    X_train, X_test, y_train, y_test = load_mnist_binary(
        n_samples=args.n_samples,
        n_features=args.n_features
    )

    # Create model
    model = VQC(n_qubits=args.n_features, depth=args.depth)

    # Train
    model = train_model(
        model, X_train, y_train,
        epochs=args.epochs,
        lr=args.lr
    )

    # Evaluate
    evaluate_model(model, X_test, y_test)

    print("\n" + "=" * 60)
    print("Training complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
