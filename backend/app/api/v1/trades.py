"""Trade endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.db.session import get_db
from app.models.user import User
from app.schemas.trade import TradeListResponse, TradeResponse
from app.dependencies import get_current_user
from app.services.portfolio_service import PortfolioService

router = APIRouter(prefix="/portfolios/{portfolio_id}/trades", tags=["trades"])


@router.get("", response_model=TradeListResponse)
async def list_trades(
    portfolio_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List trades for a portfolio with pagination"""
    service = PortfolioService(db)

    # Verify portfolio ownership
    portfolio = await service.get_portfolio_with_positions(portfolio_id, current_user.id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    # Get trades
    offset = (page - 1) * page_size
    trades, total = await service.get_portfolio_trades(portfolio_id, limit=page_size, offset=offset)

    return TradeListResponse(
        trades=[TradeResponse.model_validate(trade) for trade in trades],
        total=total,
        page=page,
        page_size=page_size
    )
