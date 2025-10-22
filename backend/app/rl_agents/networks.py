"""Neural network architectures for RL agents"""
import torch
import torch.nn as nn
from typing import Tuple


class PolicyNetwork(nn.Module):
    """
    Policy network for continuous action space (PPO)

    Outputs mean and std for Gaussian policy
    """

    def __init__(self, obs_dim: int, action_dim: int, hidden_size: int = 256):
        super().__init__()

        self.net = nn.Sequential(
            nn.Linear(obs_dim, hidden_size),
            nn.LayerNorm(hidden_size),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_size, hidden_size),
            nn.LayerNorm(hidden_size),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_size, hidden_size // 2),
            nn.LayerNorm(hidden_size // 2),
            nn.ReLU(),
        )

        # Mean head
        self.mu = nn.Linear(hidden_size // 2, action_dim)

        # Learnable log standard deviation
        self.log_std = nn.Parameter(torch.zeros(action_dim))

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass

        Args:
            x: Observation tensor (batch_size, obs_dim)

        Returns:
            (mu, std) where mu is action mean and std is action std
        """
        features = self.net(x)
        mu = self.mu(features)
        std = torch.exp(self.log_std)

        return mu, std


class ValueNetwork(nn.Module):
    """
    Value network for state value estimation (PPO critic)
    """

    def __init__(self, obs_dim: int, hidden_size: int = 256):
        super().__init__()

        self.net = nn.Sequential(
            nn.Linear(obs_dim, hidden_size),
            nn.LayerNorm(hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size),
            nn.LayerNorm(hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size // 2),
            nn.LayerNorm(hidden_size // 2),
            nn.ReLU(),
            nn.Linear(hidden_size // 2, 1)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass

        Args:
            x: Observation tensor (batch_size, obs_dim)

        Returns:
            State value (batch_size, 1)
        """
        return self.net(x)


class QNetwork(nn.Module):
    """
    Q-network for discrete action space (DQN)

    Outputs Q-values for each action
    """

    def __init__(self, obs_dim: int, action_dim: int, hidden_size: int = 256):
        super().__init__()

        self.net = nn.Sequential(
            nn.Linear(obs_dim, hidden_size),
            nn.LayerNorm(hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size),
            nn.LayerNorm(hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size // 2),
            nn.LayerNorm(hidden_size // 2),
            nn.ReLU(),
            nn.Linear(hidden_size // 2, action_dim)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass

        Args:
            x: Observation tensor (batch_size, obs_dim)

        Returns:
            Q-values for each action (batch_size, action_dim)
        """
        return self.net(x)


class ActorNetwork(nn.Module):
    """
    Actor network for A2C

    Outputs action probabilities (discrete) or action mean (continuous)
    """

    def __init__(self, obs_dim: int, action_dim: int, hidden_size: int = 256, discrete: bool = True):
        super().__init__()
        self.discrete = discrete

        self.net = nn.Sequential(
            nn.Linear(obs_dim, hidden_size),
            nn.LayerNorm(hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size),
            nn.LayerNorm(hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size // 2),
            nn.LayerNorm(hidden_size // 2),
            nn.ReLU(),
        )

        self.head = nn.Linear(hidden_size // 2, action_dim)

        if not discrete:
            # For continuous actions
            self.log_std = nn.Parameter(torch.zeros(action_dim))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass

        Args:
            x: Observation tensor (batch_size, obs_dim)

        Returns:
            For discrete: action logits (batch_size, action_dim)
            For continuous: action mean (batch_size, action_dim)
        """
        features = self.net(x)
        output = self.head(features)

        if self.discrete:
            return output  # Logits
        else:
            return output  # Mean (std is separate parameter)


class CriticNetwork(nn.Module):
    """
    Critic network for A2C

    Outputs state value
    """

    def __init__(self, obs_dim: int, hidden_size: int = 256):
        super().__init__()

        self.net = nn.Sequential(
            nn.Linear(obs_dim, hidden_size),
            nn.LayerNorm(hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size),
            nn.LayerNorm(hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size // 2),
            nn.LayerNorm(hidden_size // 2),
            nn.ReLU(),
            nn.Linear(hidden_size // 2, 1)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass

        Args:
            x: Observation tensor (batch_size, obs_dim)

        Returns:
            State value (batch_size, 1)
        """
        return self.net(x)
