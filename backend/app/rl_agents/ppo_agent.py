"""Custom PPO agent implementation"""
import torch
import torch.nn as nn
import torch.optim as optim
from torch.distributions import Normal
import numpy as np
from typing import Dict, Union
from app.rl_agents.base_agent import BaseAgent
from app.rl_agents.networks import PolicyNetwork, ValueNetwork
from app.rl_agents.replay_buffer import ReplayBatch


class PPOAgent(BaseAgent):
    """
    Proximal Policy Optimization agent

    Custom implementation for educational purposes and full control.
    Uses continuous action space with Gaussian policy.
    """

    def __init__(
        self,
        obs_dim: int,
        action_dim: int,
        action_space_type: str = "continuous",
        learning_rate: float = 3e-4,
        gamma: float = 0.99,
        gae_lambda: float = 0.95,
        clip_epsilon: float = 0.2,
        value_coef: float = 0.5,
        entropy_coef: float = 0.01,
        max_grad_norm: float = 0.5,
        n_epochs: int = 10,
        batch_size: int = 64,
        hidden_size: int = 256,
        device: str = "cpu"
    ):
        """
        Initialize PPO agent

        Args:
            obs_dim: Observation dimension
            action_dim: Action dimension
            action_space_type: Only "continuous" supported for PPO
            learning_rate: Learning rate for optimizer
            gamma: Discount factor
            gae_lambda: GAE lambda for advantage estimation
            clip_epsilon: PPO clipping parameter
            value_coef: Value loss coefficient
            entropy_coef: Entropy bonus coefficient
            max_grad_norm: Gradient clipping norm
            n_epochs: Number of PPO update epochs per batch
            batch_size: Mini-batch size for training
            hidden_size: Hidden layer size
            device: "cpu" or "cuda"
        """
        super().__init__(obs_dim, action_dim, action_space_type,
                         learning_rate=learning_rate,
                         gamma=gamma,
                         gae_lambda=gae_lambda,
                         clip_epsilon=clip_epsilon,
                         value_coef=value_coef,
                         entropy_coef=entropy_coef,
                         max_grad_norm=max_grad_norm,
                         n_epochs=n_epochs,
                         batch_size=batch_size)

        self.device = torch.device(device)
        self.gamma = gamma
        self.gae_lambda = gae_lambda
        self.clip_epsilon = clip_epsilon
        self.value_coef = value_coef
        self.entropy_coef = entropy_coef
        self.max_grad_norm = max_grad_norm
        self.n_epochs = n_epochs
        self.batch_size = batch_size

        # Networks
        self.policy = PolicyNetwork(obs_dim, action_dim, hidden_size).to(self.device)
        self.value_net = ValueNetwork(obs_dim, hidden_size).to(self.device)

        # Optimizer
        self.optimizer = optim.Adam(
            list(self.policy.parameters()) + list(self.value_net.parameters()),
            lr=learning_rate
        )

    def select_action(self, observation: np.ndarray, training: bool = True) -> np.ndarray:
        """
        Select action using policy network

        Args:
            observation: Current state
            training: If True, sample from distribution; if False, use mean

        Returns:
            Action array
        """
        with torch.no_grad():
            obs_tensor = torch.from_numpy(observation).float().unsqueeze(0).to(self.device)
            mu, std = self.policy(obs_tensor)

            if training:
                # Sample from Gaussian distribution
                dist = Normal(mu, std)
                action = dist.sample()
            else:
                # Use mean for deterministic inference
                action = mu

            # Clip to [-1, 1]
            action = torch.tanh(action)

        return action.cpu().numpy().flatten()

    def update(self, batch: ReplayBatch) -> Dict[str, float]:
        """
        Update policy using PPO algorithm

        Args:
            batch: Batch of experiences

        Returns:
            Training metrics
        """
        # Convert to tensors
        obs = torch.from_numpy(batch.observations).float().to(self.device)
        actions = torch.from_numpy(batch.actions).float().to(self.device)
        rewards = torch.from_numpy(batch.rewards).float().to(self.device)
        next_obs = torch.from_numpy(batch.next_observations).float().to(self.device)
        dones = torch.from_numpy(batch.dones).float().to(self.device)

        # Compute advantages using GAE
        with torch.no_grad():
            values = self.value_net(obs).squeeze()
            next_values = self.value_net(next_obs).squeeze()

            advantages = self._compute_gae(
                rewards, values, next_values, dones
            )

            # Returns = advantages + values (for value loss)
            returns = advantages + values

            # Normalize advantages
            advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        # Old policy log probs
        with torch.no_grad():
            mu_old, std_old = self.policy(obs)
            dist_old = Normal(mu_old, std_old)
            log_probs_old = dist_old.log_prob(actions).sum(dim=-1)

        # PPO update for multiple epochs
        total_policy_loss = 0.0
        total_value_loss = 0.0
        total_entropy = 0.0

        for epoch in range(self.n_epochs):
            # Forward pass
            mu, std = self.policy(obs)
            values_pred = self.value_net(obs).squeeze()

            # Policy loss (PPO clipped objective)
            dist = Normal(mu, std)
            log_probs = dist.log_prob(actions).sum(dim=-1)
            ratio = torch.exp(log_probs - log_probs_old)

            surr1 = ratio * advantages
            surr2 = torch.clamp(ratio, 1 - self.clip_epsilon, 1 + self.clip_epsilon) * advantages
            policy_loss = -torch.min(surr1, surr2).mean()

            # Value loss (MSE)
            value_loss = nn.MSELoss()(values_pred, returns)

            # Entropy bonus (encourage exploration)
            entropy = dist.entropy().sum(dim=-1).mean()

            # Total loss
            loss = policy_loss + self.value_coef * value_loss - self.entropy_coef * entropy

            # Backprop
            self.optimizer.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(
                list(self.policy.parameters()) + list(self.value_net.parameters()),
                self.max_grad_norm
            )
            self.optimizer.step()

            total_policy_loss += policy_loss.item()
            total_value_loss += value_loss.item()
            total_entropy += entropy.item()

        # Return metrics
        return {
            "loss": total_policy_loss / self.n_epochs,
            "value_loss": total_value_loss / self.n_epochs,
            "entropy": total_entropy / self.n_epochs,
            "reward": rewards.mean().item()
        }

    def _compute_gae(
        self,
        rewards: torch.Tensor,
        values: torch.Tensor,
        next_values: torch.Tensor,
        dones: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute Generalized Advantage Estimation

        Args:
            rewards: Reward tensor
            values: Current state values
            next_values: Next state values
            dones: Done flags

        Returns:
            Advantages tensor
        """
        advantages = torch.zeros_like(rewards)
        last_advantage = 0

        # Compute advantages backwards
        for t in reversed(range(len(rewards))):
            if t == len(rewards) - 1:
                next_value = next_values[t]
            else:
                next_value = values[t + 1]

            mask = 1.0 - dones[t]
            delta = rewards[t] + self.gamma * next_value * mask - values[t]
            advantages[t] = last_advantage = delta + self.gamma * self.gae_lambda * mask * last_advantage

        return advantages

    def save_checkpoint(self, path: str):
        """Save model checkpoint"""
        torch.save({
            "policy_state_dict": self.policy.state_dict(),
            "value_state_dict": self.value_net.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "hyperparameters": self.hyperparameters
        }, path)

    def load_checkpoint(self, path: str):
        """Load model checkpoint"""
        checkpoint = torch.load(path, map_location=self.device)
        self.policy.load_state_dict(checkpoint["policy_state_dict"])
        self.value_net.load_state_dict(checkpoint["value_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])

    @property
    def name(self) -> str:
        return "PPO"
