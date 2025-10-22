"""DQN agent skeleton for discrete action spaces"""
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from typing import Dict
from app.rl_agents.base_agent import BaseAgent
from app.rl_agents.networks import QNetwork
from app.rl_agents.replay_buffer import ReplayBatch


class DQNAgent(BaseAgent):
    """
    Deep Q-Network agent (skeleton implementation)

    For discrete action spaces (BUY/SELL/HOLD per ticker)
    """

    def __init__(
        self,
        obs_dim: int,
        action_dim: int,
        action_space_type: str = "discrete",
        learning_rate: float = 1e-3,
        gamma: float = 0.99,
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.01,
        epsilon_decay: float = 0.995,
        target_update_freq: int = 100,
        batch_size: int = 32,
        hidden_size: int = 256,
        device: str = "cpu"
    ):
        """Initialize DQN agent"""
        super().__init__(obs_dim, action_dim, action_space_type,
                         learning_rate=learning_rate,
                         gamma=gamma,
                         epsilon_start=epsilon_start,
                         epsilon_end=epsilon_end,
                         epsilon_decay=epsilon_decay,
                         target_update_freq=target_update_freq,
                         batch_size=batch_size)

        self.device = torch.device(device)
        self.gamma = gamma
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.target_update_freq = target_update_freq
        self.batch_size = batch_size

        # Q-networks (online and target)
        self.q_network = QNetwork(obs_dim, action_dim, hidden_size).to(self.device)
        self.target_network = QNetwork(obs_dim, action_dim, hidden_size).to(self.device)
        self.target_network.load_state_dict(self.q_network.state_dict())

        # Optimizer
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=learning_rate)

        self.update_count = 0

    def select_action(self, observation: np.ndarray, training: bool = True) -> int:
        """
        Select action using epsilon-greedy policy

        Args:
            observation: Current state
            training: If True, use epsilon-greedy; if False, use greedy

        Returns:
            Action index
        """
        if training and np.random.rand() < self.epsilon:
            # Random action (exploration)
            return np.random.randint(0, self.action_dim)

        # Greedy action (exploitation)
        with torch.no_grad():
            obs_tensor = torch.from_numpy(observation).float().unsqueeze(0).to(self.device)
            q_values = self.q_network(obs_tensor)
            action = q_values.argmax(dim=1).item()

        return action

    def update(self, batch: ReplayBatch) -> Dict[str, float]:
        """
        Update Q-network using DQN algorithm

        Args:
            batch: Batch of experiences

        Returns:
            Training metrics
        """
        # Convert to tensors
        obs = torch.from_numpy(batch.observations).float().to(self.device)
        actions = torch.from_numpy(batch.actions).long().to(self.device)
        rewards = torch.from_numpy(batch.rewards).float().to(self.device)
        next_obs = torch.from_numpy(batch.next_observations).float().to(self.device)
        dones = torch.from_numpy(batch.dones).float().to(self.device)

        # Current Q-values
        current_q = self.q_network(obs).gather(1, actions.unsqueeze(1)).squeeze()

        # Target Q-values (using target network)
        with torch.no_grad():
            next_q = self.target_network(next_obs).max(dim=1)[0]
            target_q = rewards + self.gamma * next_q * (1 - dones)

        # Loss (Huber loss for stability)
        loss = nn.SmoothL1Loss()(current_q, target_q)

        # Backprop
        self.optimizer.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(self.q_network.parameters(), 1.0)
        self.optimizer.step()

        # Update target network periodically
        self.update_count += 1
        if self.update_count % self.target_update_freq == 0:
            self.target_network.load_state_dict(self.q_network.state_dict())

        # Decay epsilon
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)

        return {
            "loss": loss.item(),
            "epsilon": self.epsilon,
            "reward": rewards.mean().item()
        }

    def save_checkpoint(self, path: str):
        """Save model checkpoint"""
        torch.save({
            "q_network_state_dict": self.q_network.state_dict(),
            "target_network_state_dict": self.target_network.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "epsilon": self.epsilon,
            "update_count": self.update_count,
            "hyperparameters": self.hyperparameters
        }, path)

    def load_checkpoint(self, path: str):
        """Load model checkpoint"""
        checkpoint = torch.load(path, map_location=self.device)
        self.q_network.load_state_dict(checkpoint["q_network_state_dict"])
        self.target_network.load_state_dict(checkpoint["target_network_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        self.epsilon = checkpoint.get("epsilon", self.epsilon)
        self.update_count = checkpoint.get("update_count", 0)

    @property
    def name(self) -> str:
        return "DQN"
