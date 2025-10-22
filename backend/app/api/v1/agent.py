"""Agent control endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.db.session import get_db
from app.models.user import User
from app.models.portfolio import Portfolio
from app.models.agent_run import AgentRun, AgentAlgorithm, AgentMode, ActionSpaceType, AgentStatus
from app.models.agent_metric import AgentMetric
from app.schemas.agent import (
    StartAgentRequest,
    StopAgentRequest,
    AgentStatusResponse,
    AgentRunResponse,
    AgentStatsResponse,
    AgentMetricResponse
)
from app.dependencies import get_current_user
from app.services.agent_manager import agent_manager

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/start", response_model=dict, status_code=status.HTTP_201_CREATED)
async def start_agent(
    request: StartAgentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Start an agent training or live trading session"""
    # Verify portfolio ownership
    stmt = select(Portfolio).where(
        Portfolio.id == request.portfolio_id,
        Portfolio.user_id == current_user.id
    )
    result = await db.execute(stmt)
    portfolio = result.scalar_one_or_none()

    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    # Check if agent already running for this portfolio
    stmt = select(AgentRun).where(
        AgentRun.portfolio_id == request.portfolio_id,
        AgentRun.status == AgentStatus.RUNNING
    )
    result = await db.execute(stmt)
    existing_run = result.scalar_one_or_none()

    if existing_run:
        raise HTTPException(
            status_code=400,
            detail="Agent already running for this portfolio"
        )

    # Create agent run record
    agent_run = AgentRun(
        portfolio_id=request.portfolio_id,
        algorithm=AgentAlgorithm(request.algorithm),
        mode=AgentMode(request.mode),
        action_space_type=ActionSpaceType(request.action_space_type),
        hyperparameters=request.hyperparameters,
        status=AgentStatus.RUNNING
    )

    db.add(agent_run)
    await db.commit()
    await db.refresh(agent_run)

    # Start agent via manager
    try:
        await agent_manager.start_agent(agent_run, portfolio, db)
    except Exception as e:
        # Update status to failed
        agent_run.status = AgentStatus.FAILED
        agent_run.error_message = str(e)
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to start agent: {str(e)}")

    return {
        "status": "started",
        "agent_run": AgentRunResponse.model_validate(agent_run)
    }


@router.post("/stop", status_code=status.HTTP_200_OK)
async def stop_agent(
    request: StopAgentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Stop a running agent"""
    # Verify agent run exists and user owns the portfolio
    stmt = select(AgentRun).where(AgentRun.id == request.agent_run_id)
    result = await db.execute(stmt)
    agent_run = result.scalar_one_or_none()

    if not agent_run:
        raise HTTPException(status_code=404, detail="Agent run not found")

    # Verify portfolio ownership
    stmt = select(Portfolio).where(
        Portfolio.id == agent_run.portfolio_id,
        Portfolio.user_id == current_user.id
    )
    result = await db.execute(stmt)
    portfolio = result.scalar_one_or_none()

    if not portfolio:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Stop agent
    try:
        await agent_manager.stop_agent(request.agent_run_id, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop agent: {str(e)}")

    return {"status": "stopped"}


@router.get("/status", response_model=AgentStatusResponse)
async def get_agent_status(
    portfolio_id: UUID = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get status of running agent for a portfolio"""
    # Verify portfolio ownership
    stmt = select(Portfolio).where(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    )
    result = await db.execute(stmt)
    portfolio = result.scalar_one_or_none()

    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    # Find running agent
    stmt = select(AgentRun).where(
        AgentRun.portfolio_id == portfolio_id,
        AgentRun.status == AgentStatus.RUNNING
    ).order_by(AgentRun.start_time.desc()).limit(1)
    result = await db.execute(stmt)
    agent_run = result.scalar_one_or_none()

    if not agent_run:
        return AgentStatusResponse(
            agent_run_id=None,
            status="not_running",
            algorithm=None,
            mode=None,
            last_reward=None,
            current_nav=None,
            start_time=None
        )

    status_info = await agent_manager.get_agent_status(agent_run.id, db)

    return AgentStatusResponse(**status_info)


@router.get("/{agent_run_id}/stats", response_model=AgentStatsResponse)
async def get_agent_stats(
    agent_run_id: UUID,
    limit: int = Query(1000, ge=1, le=10000),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get agent statistics and metrics"""
    # Verify agent run exists and user owns portfolio
    stmt = select(AgentRun).where(AgentRun.id == agent_run_id)
    result = await db.execute(stmt)
    agent_run = result.scalar_one_or_none()

    if not agent_run:
        raise HTTPException(status_code=404, detail="Agent run not found")

    # Verify portfolio ownership
    stmt = select(Portfolio).where(
        Portfolio.id == agent_run.portfolio_id,
        Portfolio.user_id == current_user.id
    )
    result = await db.execute(stmt)
    portfolio = result.scalar_one_or_none()

    if not portfolio:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get metrics
    stmt = select(AgentMetric).where(
        AgentMetric.agent_run_id == agent_run_id
    ).order_by(AgentMetric.timestamp.asc()).limit(limit)
    result = await db.execute(stmt)
    metrics = result.scalars().all()

    # Get total count
    from sqlalchemy import func
    count_stmt = select(func.count()).select_from(AgentMetric).where(
        AgentMetric.agent_run_id == agent_run_id
    )
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()

    return AgentStatsResponse(
        agent_run=AgentRunResponse.model_validate(agent_run),
        metrics=[AgentMetricResponse.model_validate(m) for m in metrics],
        total_metrics=total
    )
