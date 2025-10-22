"""Portfolio endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
from app.db.session import get_db
from app.models.user import User
from app.models.portfolio import Portfolio
from app.schemas.portfolio import (
    PortfolioCreate,
    PortfolioUpdate,
    PortfolioResponse,
    PortfolioListResponse,
    PositionResponse
)
from app.dependencies import get_current_user
from app.services.portfolio_service import PortfolioService

router = APIRouter(prefix="/portfolios", tags=["portfolios"])


@router.get("", response_model=PortfolioListResponse)
async def list_portfolios(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all portfolios for current user"""
    service = PortfolioService(db)
    portfolios = await service.get_user_portfolios(current_user.id)

    # Compute metrics for each portfolio
    portfolio_responses = []
    for portfolio in portfolios:
        metrics = await service.compute_portfolio_metrics(portfolio)
        portfolio_responses.append(
            PortfolioResponse(
                id=portfolio.id,
                user_id=portfolio.user_id,
                name=portfolio.name,
                initial_budget=portfolio.initial_budget,
                current_cash=portfolio.current_cash,
                tickers=portfolio.tickers,
                allocation_strategy=portfolio.allocation_strategy,
                risk_profile=portfolio.risk_profile.value,
                is_active=portfolio.is_active,
                nav=metrics["nav"],
                pnl=metrics["pnl"],
                pnl_percent=metrics["pnl_percent"],
                created_at=portfolio.created_at,
                updated_at=portfolio.updated_at
            )
        )

    return PortfolioListResponse(portfolios=portfolio_responses)


@router.post("", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    portfolio_data: PortfolioCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new portfolio"""
    service = PortfolioService(db)

    # Validate tickers
    ticker_validation = await service.validate_tickers(portfolio_data.tickers)
    invalid_tickers = [t for t, valid in ticker_validation.items() if not valid]
    if invalid_tickers:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid tickers: {', '.join(invalid_tickers)}"
        )

    # Create portfolio
    portfolio = await service.create_portfolio(
        user_id=current_user.id,
        portfolio_data=portfolio_data.model_dump()
    )

    # Compute initial metrics
    metrics = await service.compute_portfolio_metrics(portfolio)

    return PortfolioResponse(
        id=portfolio.id,
        user_id=portfolio.user_id,
        name=portfolio.name,
        initial_budget=portfolio.initial_budget,
        current_cash=portfolio.current_cash,
        tickers=portfolio.tickers,
        allocation_strategy=portfolio.allocation_strategy,
        risk_profile=portfolio.risk_profile.value,
        is_active=portfolio.is_active,
        nav=metrics["nav"],
        pnl=metrics["pnl"],
        pnl_percent=metrics["pnl_percent"],
        created_at=portfolio.created_at,
        updated_at=portfolio.updated_at
    )


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(
    portfolio_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get portfolio by ID"""
    service = PortfolioService(db)
    portfolio = await service.get_portfolio_with_positions(portfolio_id, current_user.id)

    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    # Compute metrics
    metrics = await service.compute_portfolio_metrics(portfolio)

    # Format positions
    positions = [
        PositionResponse(**pos)
        for pos in metrics["positions"]
    ]

    return PortfolioResponse(
        id=portfolio.id,
        user_id=portfolio.user_id,
        name=portfolio.name,
        initial_budget=portfolio.initial_budget,
        current_cash=portfolio.current_cash,
        tickers=portfolio.tickers,
        allocation_strategy=portfolio.allocation_strategy,
        risk_profile=portfolio.risk_profile.value,
        is_active=portfolio.is_active,
        nav=metrics["nav"],
        pnl=metrics["pnl"],
        pnl_percent=metrics["pnl_percent"],
        positions=positions,
        created_at=portfolio.created_at,
        updated_at=portfolio.updated_at
    )


@router.patch("/{portfolio_id}", response_model=PortfolioResponse)
async def update_portfolio(
    portfolio_id: UUID,
    update_data: PortfolioUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update portfolio"""
    service = PortfolioService(db)
    portfolio = await service.get_portfolio_with_positions(portfolio_id, current_user.id)

    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    # Validate tickers if provided
    if update_data.tickers:
        ticker_validation = await service.validate_tickers(update_data.tickers)
        invalid_tickers = [t for t, valid in ticker_validation.items() if not valid]
        if invalid_tickers:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid tickers: {', '.join(invalid_tickers)}"
            )

    # Update portfolio
    portfolio = await service.update_portfolio(
        portfolio,
        update_data.model_dump(exclude_unset=True)
    )

    # Compute metrics
    metrics = await service.compute_portfolio_metrics(portfolio)

    return PortfolioResponse(
        id=portfolio.id,
        user_id=portfolio.user_id,
        name=portfolio.name,
        initial_budget=portfolio.initial_budget,
        current_cash=portfolio.current_cash,
        tickers=portfolio.tickers,
        allocation_strategy=portfolio.allocation_strategy,
        risk_profile=portfolio.risk_profile.value,
        is_active=portfolio.is_active,
        nav=metrics["nav"],
        pnl=metrics["pnl"],
        pnl_percent=metrics["pnl_percent"],
        created_at=portfolio.created_at,
        updated_at=portfolio.updated_at
    )


@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio(
    portfolio_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete portfolio"""
    service = PortfolioService(db)
    portfolio = await service.get_portfolio_with_positions(portfolio_id, current_user.id)

    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    await service.delete_portfolio(portfolio)
