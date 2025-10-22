"""Base agent interface for RL algorithms"""
from abc import ABC, abstractmethod
from typing import Dict, Union
import numpy as np


class BaseAgent(ABC):
    """Abstract base class for all RL agents"""

    def __init__(
        self,
        obs_dim: int,
        action_dim: int,
        action_space_type: str,
        **kwargs
    ):
        """
        Initialize agent

        Args:
            obs_dim: Observation space dimension
            action_dim: Action space dimension
            action_space_type: "discrete" or "continuous"
            **kwargs: Additional hyperparameters
        """
        self.obs_dim = obs_dim
        self.action_dim = action_dim
        self.action_space_type = action_space_type
        self.hyperparameters = kwargs

    @abstractmethod
    def select_action(self, observation: np.ndarray, training: bool = True) -> Union[int, np.ndarray]:
        """
        Select action given observation

        Args:
            observation: Current state observation
            training: If True, use exploration; if False, use exploitation

        Returns:
            For discrete: integer action index
            For continuous: numpy array of action values
        """
        pass

    @abstractmethod
    def update(self, batch: 'ReplayBatch') -> Dict[str, float]:
        """
        Train agent on a batch of experiences

        Args:
            batch: Batch of transitions from replay buffer

        Returns:
            Dictionary of training metrics (e.g., {'loss': 0.5, 'reward': 10.0})
        """
        pass

    @abstractmethod
    def save_checkpoint(self, path: str):
        """Save model weights to file"""
        pass

    @abstractmethod
    def load_checkpoint(self, path: str):
        """Load model weights from file"""
        pass

    def get_config(self) -> dict:
        """Return agent configuration"""
        return {
            "name": self.name,
            "obs_dim": self.obs_dim,
            "action_dim": self.action_dim,
            "action_space_type": self.action_space_type,
            "hyperparameters": self.hyperparameters
        }

    @property
    @abstractmethod
    def name(self) -> str:
        """Agent algorithm name"""
        pass
