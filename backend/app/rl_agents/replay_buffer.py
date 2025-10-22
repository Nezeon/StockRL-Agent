"""Experience replay buffer for RL training"""
from dataclasses import dataclass
from typing import List, Tuple
import numpy as np
import random


@dataclass
class ReplayBatch:
    """Batch of experiences sampled from replay buffer"""
    observations: np.ndarray
    actions: np.ndarray
    rewards: np.ndarray
    next_observations: np.ndarray
    dones: np.ndarray


class ReplayBuffer:
    """
    Circular replay buffer for storing experiences

    Stores transitions (s, a, r, s', done) for off-policy RL algorithms
    """

    def __init__(self, capacity: int, obs_dim: int, action_dim: int):
        """
        Initialize replay buffer

        Args:
            capacity: Maximum number of transitions to store
            obs_dim: Observation dimension
            action_dim: Action dimension
        """
        self.capacity = capacity
        self.obs_dim = obs_dim
        self.action_dim = action_dim

        # Preallocate arrays
        self.observations = np.zeros((capacity, obs_dim), dtype=np.float32)
        self.actions = np.zeros((capacity, action_dim), dtype=np.float32)
        self.rewards = np.zeros(capacity, dtype=np.float32)
        self.next_observations = np.zeros((capacity, obs_dim), dtype=np.float32)
        self.dones = np.zeros(capacity, dtype=np.float32)

        self.position = 0
        self.size = 0

    def add(
        self,
        obs: np.ndarray,
        action: np.ndarray,
        reward: float,
        next_obs: np.ndarray,
        done: bool
    ):
        """Add a transition to the buffer"""
        self.observations[self.position] = obs
        self.actions[self.position] = action
        self.rewards[self.position] = reward
        self.next_observations[self.position] = next_obs
        self.dones[self.position] = float(done)

        self.position = (self.position + 1) % self.capacity
        self.size = min(self.size + 1, self.capacity)

    def sample(self, batch_size: int) -> ReplayBatch:
        """
        Sample a random batch of transitions

        Args:
            batch_size: Number of transitions to sample

        Returns:
            ReplayBatch with sampled experiences
        """
        if self.size < batch_size:
            raise ValueError(f"Not enough samples: have {self.size}, need {batch_size}")

        indices = np.random.randint(0, self.size, size=batch_size)

        return ReplayBatch(
            observations=self.observations[indices],
            actions=self.actions[indices],
            rewards=self.rewards[indices],
            next_observations=self.next_observations[indices],
            dones=self.dones[indices]
        )

    def __len__(self) -> int:
        return self.size

    def clear(self):
        """Clear the buffer"""
        self.position = 0
        self.size = 0
