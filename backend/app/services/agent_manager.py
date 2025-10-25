"""Agent manager service - orchestrates agent training and live trading"""
import asyncio
from decimal import Decimal
from typing import Dict, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.portfolio import Portfolio
from app.models.agent_run import AgentRun, AgentStatus
from app.models.agent_metric import AgentMetric
from app.rl_agents.ppo_agent import PPOAgent
from app.rl_agents.dqn_agent import DQNAgent
from app.rl_agents.a2c_agent import A2CAgent
from app.rl_agents.environment import TradingEnvironment
from app.rl_agents.observation import ObservationBuilder
from app.data_providers.registry import get_provider
from app.config import settings
from app.db.session import AsyncSessionLocal
import os


class AgentManager:
    """
    Manages agent lifecycle - training and live trading

    Responsibilities:
    - Start/stop agents
    - Run training loops
    - Execute live trading
    - Track metrics and save checkpoints
    """

    def __init__(self):
        self.running_agents: Dict[UUID, asyncio.Task] = {}
        self.agent_instances: Dict[UUID, object] = {}

    async def start_agent(
        self,
        agent_run: AgentRun,
        portfolio: Portfolio,
        db: AsyncSession
    ) -> UUID:
        """
        Start an agent training or live trading session

        Args:
            agent_run: AgentRun database record
            portfolio: Portfolio to trade
            db: Database session

        Returns:
            Agent run ID
        """
        # Create agent instance
        agent = self._create_agent(
            algorithm=agent_run.algorithm.value,
            obs_dim=self._calculate_obs_dim(portfolio.tickers),
            action_dim=self._calculate_action_dim(portfolio.tickers, agent_run.action_space_type.value),
            action_space_type=agent_run.action_space_type.value,
            hyperparameters=agent_run.hyperparameters or {}
        )

        # Store agent instance
        self.agent_instances[agent_run.id] = agent

        # Start agent task
        if agent_run.mode.value == "train":
            task = asyncio.create_task(
                self._run_training(agent_run.id, agent, portfolio, db)
            )
        else:  # live
            task = asyncio.create_task(
                self._run_live_trading(agent_run.id, agent, portfolio, db)
            )

        self.running_agents[agent_run.id] = task

        return agent_run.id

    async def stop_agent(self, agent_run_id: UUID, db: AsyncSession):
        """Stop a running agent"""
        # Cancel task if it's tracked in memory
        if agent_run_id in self.running_agents:
            task = self.running_agents[agent_run_id]
            task.cancel()

            try:
                await task
            except asyncio.CancelledError:
                pass

            # Cleanup task bookkeeping
            del self.running_agents[agent_run_id]
            if agent_run_id in self.agent_instances:
                del self.agent_instances[agent_run_id]

        # Always update DB status even if the task wasn't found (treat as stale)
        stmt = select(AgentRun).where(AgentRun.id == agent_run_id)
        result = await db.execute(stmt)
        agent_run = result.scalar_one_or_none()

        if agent_run and agent_run.status != AgentStatus.STOPPED:
            agent_run.status = AgentStatus.STOPPED
            agent_run.end_time = datetime.utcnow()
            await db.commit()

    async def get_agent_status(self, agent_run_id: UUID, db: AsyncSession) -> Dict:
        """Get status of an agent run"""
        stmt = select(AgentRun).where(AgentRun.id == agent_run_id)
        result = await db.execute(stmt)
        agent_run = result.scalar_one_or_none()

        if not agent_run:
            return {"status": "not_found"}

        # Get latest metric
        latest_metric_stmt = select(AgentMetric).where(
            AgentMetric.agent_run_id == agent_run_id
        ).order_by(AgentMetric.timestamp.desc()).limit(1)
        metric_result = await db.execute(latest_metric_stmt)
        latest_metric = metric_result.scalar_one_or_none()

        return {
            "agent_run_id": agent_run.id,
            "status": agent_run.status.value,
            "algorithm": agent_run.algorithm.value,
            "mode": agent_run.mode.value,
            "start_time": agent_run.start_time,
            "last_reward": float(latest_metric.cumulative_reward) if latest_metric else None,
            "current_nav": float(latest_metric.portfolio_nav) if latest_metric else None,
            "step": latest_metric.step if latest_metric else 0
        }

    def _create_agent(
        self,
        algorithm: str,
        obs_dim: int,
        action_dim: int,
        action_space_type: str,
        hyperparameters: dict
    ):
        """Create agent instance based on algorithm"""
        # Filter hyperparameters to only include valid ones for each agent
        valid_ppo_params = {
            'learning_rate', 'gamma', 'gae_lambda', 'clip_epsilon', 
            'value_coef', 'entropy_coef', 'max_grad_norm', 'n_epochs', 
            'batch_size', 'hidden_size', 'device'
        }
        valid_dqn_params = {
            'learning_rate', 'gamma', 'epsilon_start', 'epsilon_end', 
            'epsilon_decay', 'target_update_freq', 'batch_size', 
            'hidden_size', 'buffer_size', 'device'
        }
        valid_a2c_params = {
            'learning_rate', 'gamma', 'value_coef', 'entropy_coef', 
            'max_grad_norm', 'hidden_size', 'device'
        }
        
        if algorithm == "PPO":
            filtered_params = {k: v for k, v in hyperparameters.items() if k in valid_ppo_params}
            return PPOAgent(
                obs_dim=obs_dim,
                action_dim=action_dim,
                action_space_type=action_space_type,
                **filtered_params
            )
        elif algorithm == "DQN":
            filtered_params = {k: v for k, v in hyperparameters.items() if k in valid_dqn_params}
            return DQNAgent(
                obs_dim=obs_dim,
                action_dim=action_dim,
                action_space_type=action_space_type,
                **filtered_params
            )
        elif algorithm == "A2C":
            filtered_params = {k: v for k, v in hyperparameters.items() if k in valid_a2c_params}
            return A2CAgent(
                obs_dim=obs_dim,
                action_dim=action_dim,
                action_space_type=action_space_type,
                **filtered_params
            )
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")

    async def _run_training(
        self,
        agent_run_id: UUID,
        agent,
        portfolio: Portfolio,
        db: AsyncSession
    ):
        """Run agent training loop with interim metric logging for real-time feedback"""
        try:
            # Debug log file
            try:
                with open(os.path.join(os.getcwd(), "training_debug.log"), "a", encoding="utf-8") as f:
                    f.write(f"START _run_training run={agent_run_id} at {datetime.utcnow().isoformat()}\n")
            except Exception:
                pass
            # Create trading environment
            data_provider = get_provider()
            env = TradingEnvironment(
                portfolio_id=portfolio.id,
                data_provider=data_provider,
                tickers=portfolio.tickers,
                initial_cash=float(portfolio.initial_budget),
                risk_profile=portfolio.risk_profile.value,
                action_space_type=agent.action_space_type,
                # Allow overriding from hyperparameters for faster feedback
                max_steps=int(agent.hyperparameters.get("max_steps", 1000))
            )

            # Training parameters
            episodes = int(agent.hyperparameters.get("episodes", 100))
            save_interval = 10  # Save checkpoint every 10 episodes
            log_interval = int(agent.hyperparameters.get("log_interval", 25))
            if log_interval <= 0:
                log_interval = 25

            for episode in range(episodes):
                # Check if cancelled
                if agent_run_id not in self.running_agents:
                    break

                # Reset environment
                observation = await env.reset()
                episode_reward = 0.0
                done = False
                step = 0

                # Warm-start metric so UI shows activity immediately
                try:
                    await self._log_metric(agent_run_id, step, 0.0, env._compute_nav(), db)
                    try:
                        with open(os.path.join(os.getcwd(), "training_debug.log"), "a", encoding="utf-8") as f:
                            f.write(f"LOG warm-start run={agent_run_id} step={step}\n")
                    except Exception:
                        pass
                except Exception:
                    pass

                # Accumulate reward deltas between logs to keep cumulative accurate
                interval_reward_accum = 0.0

                while not done:
                    # Select action
                    action = agent.select_action(observation, training=True)

                    # Take step
                    next_observation, reward, done, info = await env.step(action)

                    episode_reward += reward
                    interval_reward_accum += reward
                    step += 1

                    # Advance observation
                    observation = next_observation

                    # Emit interim metrics every N steps to provide real-time feedback
                    if step % log_interval == 0:
                        try:
                            await self._log_metric(
                                agent_run_id,
                                step,
                                interval_reward_accum,
                                info["nav"],
                                db
                            )
                            try:
                                with open(os.path.join(os.getcwd(), "training_debug.log"), "a", encoding="utf-8") as f:
                                    f.write(f"LOG interim run={agent_run_id} step={step}\n")
                            except Exception:
                                pass
                        finally:
                            interval_reward_accum = 0.0

                    # Yield occasionally to avoid starving the event loop on long episodes
                    if step % 100 == 0:
                        await asyncio.sleep(0)

                # Log any remaining accumulated reward at episode end (without double-counting)
                if interval_reward_accum != 0.0:
                    try:
                        await self._log_metric(agent_run_id, step, interval_reward_accum, info["nav"], db)
                        try:
                            with open(os.path.join(os.getcwd(), "training_debug.log"), "a", encoding="utf-8") as f:
                                f.write(f"LOG final-chunk run={agent_run_id} step={step}\n")
                        except Exception:
                            pass
                    finally:
                        interval_reward_accum = 0.0

                # Save checkpoint periodically
                if (episode + 1) % save_interval == 0:
                    self._save_checkpoint(agent_run_id, agent)

            # Mark as completed
            await self._complete_agent_run(agent_run_id, env._compute_nav(), db)

        except Exception as e:
            # Mark as failed
            await self._fail_agent_run(agent_run_id, str(e), db)
            try:
                with open(os.path.join(os.getcwd(), "training_debug.log"), "a", encoding="utf-8") as f:
                    f.write(f"ERROR run={agent_run_id} err={e}\n")
            except Exception:
                pass
            raise

    async def _run_live_trading(
        self,
        agent_run_id: UUID,
        agent,
        portfolio: Portfolio,
        db: AsyncSession
    ):
        """Run live trading (using trained agent)"""
        try:
            # Load checkpoint if exists
            checkpoint_path = self._get_checkpoint_path(agent_run_id)
            if os.path.exists(checkpoint_path):
                agent.load_checkpoint(checkpoint_path)

            # Create trading environment
            data_provider = get_provider()
            env = TradingEnvironment(
                portfolio_id=portfolio.id,
                data_provider=data_provider,
                tickers=portfolio.tickers,
                initial_cash=float(portfolio.current_cash),
                risk_profile=portfolio.risk_profile.value,
                action_space_type=agent.action_space_type,
                max_steps=10000  # Run indefinitely
            )

            # Live trading loop
            observation = await env.reset()
            step = 0

            while agent_run_id in self.running_agents:
                # Select action (deterministic for live trading)
                action = agent.select_action(observation, training=False)

                # Execute action
                next_observation, reward, done, info = await env.step(action)

                step += 1

                # Log metrics periodically
                if step % 10 == 0:
                    await self._log_metric(
                        agent_run_id,
                        step,
                        reward,
                        info["nav"],
                        db
                    )

                observation = next_observation

                # Sleep to avoid excessive trading
                await asyncio.sleep(60)  # 1 minute intervals

                if done:
                    observation = await env.reset()

        except Exception as e:
            await self._fail_agent_run(agent_run_id, str(e), db)
            raise

    async def _log_metric(
        self,
        agent_run_id: UUID,
        step: int,
        reward: float,
        nav: float,
        db: AsyncSession
    ):
        """Log agent metric to database"""
        # Always use a fresh DB session for background logging to avoid request-scope session issues
        async with AsyncSessionLocal() as _db:
            # Get cumulative reward
            stmt = select(AgentMetric).where(
                AgentMetric.agent_run_id == agent_run_id
            ).order_by(AgentMetric.timestamp.desc()).limit(1)
            result = await _db.execute(stmt)
            last_metric = result.scalar_one_or_none()

            cumulative_reward = reward
            if last_metric:
                cumulative_reward += float(last_metric.cumulative_reward)

            metric = AgentMetric(
                agent_run_id=agent_run_id,
                step=step,
                episode_reward=Decimal(str(reward)),
                cumulative_reward=Decimal(str(cumulative_reward)),
                loss=None,  # TODO: Track loss
                portfolio_nav=Decimal(str(nav)),
                rolling_sharpe=None  # TODO: Calculate Sharpe
            )

            _db.add(metric)
            await _db.commit()
        
        # Broadcast metric update via WebSocket
        from app.api.websocket import broadcast_agent_metric
        try:
            await broadcast_agent_metric(agent_run_id, {
                "step": step,
                "episode_reward": float(reward),
                "cumulative_reward": float(cumulative_reward),
                "portfolio_nav": float(nav)
            })
        except Exception as e:
            # Don't fail metric logging if broadcast fails
            print(f"Failed to broadcast agent metric: {e}")

    async def _complete_agent_run(self, agent_run_id: UUID, final_nav: float, db: AsyncSession):
        """Mark agent run as completed"""
        async with AsyncSessionLocal() as _db:
            stmt = select(AgentRun).where(AgentRun.id == agent_run_id)
            result = await _db.execute(stmt)
            agent_run = result.scalar_one_or_none()

            if agent_run:
                agent_run.status = AgentStatus.COMPLETED
                agent_run.end_time = datetime.utcnow()
                agent_run.final_nav = Decimal(str(final_nav))
                await _db.commit()

    async def _fail_agent_run(self, agent_run_id: UUID, error_message: str, db: AsyncSession):
        """Mark agent run as failed"""
        async with AsyncSessionLocal() as _db:
            stmt = select(AgentRun).where(AgentRun.id == agent_run_id)
            result = await _db.execute(stmt)
            agent_run = result.scalar_one_or_none()

            if agent_run:
                agent_run.status = AgentStatus.FAILED
                agent_run.end_time = datetime.utcnow()
                agent_run.error_message = error_message
                await _db.commit()

    def _save_checkpoint(self, agent_run_id: UUID, agent):
        """Save agent checkpoint"""
        os.makedirs(settings.checkpoint_dir, exist_ok=True)
        checkpoint_path = self._get_checkpoint_path(agent_run_id)
        agent.save_checkpoint(checkpoint_path)

    def _get_checkpoint_path(self, agent_run_id: UUID) -> str:
        """Get checkpoint file path for agent run"""
        return os.path.join(settings.checkpoint_dir, f"agent_{agent_run_id}.pt")

    def _calculate_obs_dim(self, tickers: list) -> int:
        """Calculate observation dimension"""
        builder = ObservationBuilder(tickers, lookback_window=30)
        return builder.get_observation_dim()

    def _calculate_action_dim(self, tickers: list, action_space_type: str) -> int:
        """Calculate action dimension"""
        if action_space_type == "discrete":
            return 3 ** len(tickers)  # HOLD, BUY, SELL per ticker
        else:  # continuous
            return len(tickers)  # One value per ticker


# Global agent manager instance
agent_manager = AgentManager()
