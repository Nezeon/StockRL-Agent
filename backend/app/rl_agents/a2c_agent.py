"""A2C agent skeleton for both discrete and continuous actions"""
import torch
import torch.nn as nn
import torch.optim as optim
from torch.distributions import Categorical, Normal
import numpy as np
from typing import Dict, Union
from app.rl_agents.base_agent import BaseAgent
from app.rl_agents.networks import ActorNetwork, CriticNetwork
from app.rl_agents.replay_buffer import ReplayBatch


class A2CAgent(BaseAgent):
    """
    Advantage Actor-Critic agent (skeleton implementation)

    Supports both discrete and continuous action spaces
    """

    def __init__(
        self,
        obs_dim: int,
        action_dim: int,
        action_space_type: str = "continuous",
        learning_rate: float = 3e-4,
        gamma: float = 0.99,
        value_coef: float = 0.5,
        entropy_coef: float = 0.01,
        max_grad_norm: float = 0.5,
        hidden_size: int = 256,
        device: str = "cpu"
    ):
        """Initialize A2C agent"""
        super().__init__(obs_dim, action_dim, action_space_type,
                         learning_rate=learning_rate,
                         gamma=gamma,
                         value_coef=value_coef,
                         entropy_coef=entropy_coef,
                         max_grad_norm=max_grad_norm)

        self.device = torch.device(device)
        self.gamma = gamma
        self.value_coef = value_coef
        self.entropy_coef = entropy_coef
        self.max_grad_norm = max_grad_norm

        # Networks
        is_discrete = (action_space_type == "discrete")
        self.actor = ActorNetwork(obs_dim, action_dim, hidden_size, discrete=is_discrete).to(self.device)
        self.critic = CriticNetwork(obs_dim, hidden_size).to(self.device)

        # Optimizer
        self.optimizer = optim.Adam(
            list(self.actor.parameters()) + list(self.critic.parameters()),
            lr=learning_rate
        )

    def select_action(self, observation: np.ndarray, training: bool = True) -> Union[int, np.ndarray]:
        """
        Select action using actor network

        Args:
            observation: Current state
            training: If True, sample; if False, use deterministic action

        Returns:
            Action (int for discrete, array for continuous)
        """
        with torch.no_grad():
            obs_tensor = torch.from_numpy(observation).float().unsqueeze(0).to(self.device)

            if self.action_space_type == "discrete":
                logits = self.actor(obs_tensor)
                if training:
                    dist = Categorical(logits=logits)
                    action = dist.sample()
                else:
                    action = logits.argmax(dim=1)
                return action.item()
            else:  # continuous
                mu = self.actor(obs_tensor)
                if training:
                    std = torch.exp(self.actor.log_std)
                    dist = Normal(mu, std)
                    action = dist.sample()
                else:
                    action = mu
                action = torch.tanh(action)
                return action.cpu().numpy().flatten()

    def update(self, batch: ReplayBatch) -> Dict[str, float]:
        """
        Update actor and critic using A2C algorithm

        Args:
            batch: Batch of experiences

        Returns:
            Training metrics
        """
        # Convert to tensors
        obs = torch.from_numpy(batch.observations).float().to(self.device)
        actions = torch.from_numpy(batch.actions).to(self.device)
        rewards = torch.from_numpy(batch.rewards).float().to(self.device)
        next_obs = torch.from_numpy(batch.next_observations).float().to(self.device)
        dones = torch.from_numpy(batch.dones).float().to(self.device)

        # Compute values
        values = self.critic(obs).squeeze()
        next_values = self.critic(next_obs).squeeze()

        # Compute advantages
        with torch.no_grad():
            advantages = rewards + self.gamma * next_values * (1 - dones) - values

        # Actor loss (policy gradient)
        if self.action_space_type == "discrete":
            logits = self.actor(obs)
            dist = Categorical(logits=logits)
            log_probs = dist.log_prob(actions.long())
            entropy = dist.entropy().mean()
        else:  # continuous
            mu = self.actor(obs)
            std = torch.exp(self.actor.log_std)
            dist = Normal(mu, std)
            log_probs = dist.log_prob(actions.float()).sum(dim=-1)
            entropy = dist.entropy().sum(dim=-1).mean()

        actor_loss = -(log_probs * advantages.detach()).mean()

        # Critic loss (value function)
        targets = rewards + self.gamma * next_values.detach() * (1 - dones)
        critic_loss = nn.MSELoss()(values, targets)

        # Total loss
        loss = actor_loss + self.value_coef * critic_loss - self.entropy_coef * entropy

        # Backprop
        self.optimizer.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(
            list(self.actor.parameters()) + list(self.critic.parameters()),
            self.max_grad_norm
        )
        self.optimizer.step()

        return {
            "loss": actor_loss.item(),
            "critic_loss": critic_loss.item(),
            "entropy": entropy.item(),
            "reward": rewards.mean().item()
        }

    def save_checkpoint(self, path: str):
        """Save model checkpoint"""
        torch.save({
            "actor_state_dict": self.actor.state_dict(),
            "critic_state_dict": self.critic.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "hyperparameters": self.hyperparameters
        }, path)

    def load_checkpoint(self, path: str):
        """Load model checkpoint"""
        checkpoint = torch.load(path, map_location=self.device)
        self.actor.load_state_dict(checkpoint["actor_state_dict"])
        self.critic.load_state_dict(checkpoint["critic_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])

    @property
    def name(self) -> str:
        return "A2C"
