from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.db.session import get_db
from app.db.models import Investment, WithdrawalRequest, User, UserRole, Startup
from app.core.dependencies import get_current_user, require_role
from app.utils.logger import logger

router = APIRouter(prefix="/api/escrow", tags=["escrow"])


class ReleaseFundsRequest(BaseModel):
    investment_id: int
    amount: float


class WithdrawalRequestCreate(BaseModel):
    startup_id: Optional[int] = None
    investment_id: Optional[int] = None
    amount: float
    reason: str


class WithdrawalRequestUpdate(BaseModel):
    status: str  # approved, rejected
    admin_feedback: Optional[str] = None


class WithdrawalRequestResponse(BaseModel):
    id: int
    startup_id: Optional[int] = None
    investor_id: Optional[int] = None
    investment_id: Optional[int] = None
    request_type: str
    amount: float
    reason: str
    status: str
    admin_feedback: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/release", status_code=status.HTTP_200_OK)
async def release_funds(
    body: ReleaseFundsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Investor releases funds from escrow to the startup's withdrawable balance."""
    investment = db.query(Investment).filter(Investment.id == body.investment_id).first()
    if not investment:
        raise HTTPException(status_code=404, detail="Investment not found")

    if investment.investor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the investor can release these funds")

    if body.amount <= 0:
        raise HTTPException(status_code=400, detail="Release amount must be positive")

    if body.amount > investment.escrow_balance:
        raise HTTPException(status_code=400, detail="Insufficient escrow balance")

    # Check for pending investor reclaim requests on this investment
    pending_reclaims = db.query(WithdrawalRequest).filter(
        WithdrawalRequest.investment_id == investment.id,
        WithdrawalRequest.request_type == "investor_reclaim",
        WithdrawalRequest.status == "pending"
    ).all()
    reclaimed_sum = sum(req.amount for req in pending_reclaims)

    if body.amount > (investment.escrow_balance - reclaimed_sum):
        raise HTTPException(status_code=400, detail="Escrow balance is partially locked by pending reclaim requests")

    investment.escrow_balance -= body.amount
    investment.released_amount += body.amount

    # Update startup's withdrawable balance
    startup = investment.startup
    startup.withdrawable_balance = (startup.withdrawable_balance or 0.0) + body.amount

    db.commit()

    logger.info(f"Investor {current_user.id} released {body.amount} for investment {investment.id}")
    return {"message": f"Successfully released {body.amount} to startup", "new_escrow_balance": investment.escrow_balance}


@router.post("/investor-withdraw-request", response_model=WithdrawalRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_investor_withdrawal_request(
    body: WithdrawalRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Investor requests to reclaim funds from escrow."""
    if not body.investment_id:
        raise HTTPException(status_code=400, detail="investment_id is required")

    investment = db.query(Investment).filter(Investment.id == body.investment_id).first()
    if not investment:
        raise HTTPException(status_code=404, detail="Investment not found")

    if investment.investor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the investor of this investment can request a reclaim")

    if body.amount <= 0:
        raise HTTPException(status_code=400, detail="Reclaim amount must be positive")

    # Check available escrow balance (minus pending reclaims and minus what might be released??)
    # Releasing funds immediately decrements escrow_balance.
    # So we just need to check pending reclaims.
    pending_reclaims = db.query(WithdrawalRequest).filter(
        WithdrawalRequest.investment_id == body.investment_id,
        WithdrawalRequest.request_type == "investor_reclaim",
        WithdrawalRequest.status == "pending"
    ).all()
    pending_sum = sum(req.amount for req in pending_reclaims)

    available = investment.escrow_balance - pending_sum
    if body.amount > available:
         raise HTTPException(status_code=400, detail=f"Insufficient available escrow balance. Escrow: {investment.escrow_balance}, Pending Reclaims: {pending_sum}")

    request = WithdrawalRequest(
        investor_id=current_user.id,
        investment_id=body.investment_id,
        request_type="investor_reclaim",
        amount=body.amount,
        reason=body.reason,
        status="pending"
    )
    db.add(request)
    db.commit()
    db.refresh(request)

    logger.info(f"Investor {current_user.id} created reclaim request for {body.amount} from investment {body.investment_id}")
    return request


@router.post("/withdraw-request", response_model=WithdrawalRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_withdrawal_request(
    body: WithdrawalRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Startup founder requests to withdraw released funds."""
    startup = db.query(Startup).filter(Startup.id == body.startup_id).first()
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")

    if startup.founder_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the startup founder can request withdrawals")

    # Check available balance (withdrawable_balance - pending requests)
    pending_requests = db.query(WithdrawalRequest).filter(
        WithdrawalRequest.startup_id == body.startup_id,
        WithdrawalRequest.request_type == "startup_withdrawal",
        WithdrawalRequest.status == "pending"
    ).all()
    pending_sum = sum(req.amount for req in pending_requests)

    available = (startup.withdrawable_balance or 0.0) - pending_sum

    if body.amount > available:
         raise HTTPException(status_code=400, detail=f"Insufficient available balance. Withdrawable: {startup.withdrawable_balance}, Pending: {pending_sum}")

    request = WithdrawalRequest(
        startup_id=body.startup_id,
        request_type="startup_withdrawal",
        amount=body.amount,
        reason=body.reason,
        status="pending"
    )
    db.add(request)
    db.commit()
    db.refresh(request)

    logger.info(f"Startup {body.startup_id} created withdrawal request for {body.amount}")
    return request


@router.get("/admin/withdraw-requests", response_model=List[WithdrawalRequestResponse])
async def get_all_withdrawal_requests(
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Admin views all withdrawal requests."""
    return db.query(WithdrawalRequest).all()


@router.post("/admin/withdraw-requests/{request_id}/review", response_model=WithdrawalRequestResponse)
async def review_withdrawal_request(
    request_id: int,
    body: WithdrawalRequestUpdate,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Admin approves or rejects a withdrawal request."""
    request = db.query(WithdrawalRequest).filter(WithdrawalRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Withdrawal request not found")

    if request.status != "pending":
        raise HTTPException(status_code=400, detail="Request already reviewed")

    if body.status not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="Status must be 'approved' or 'rejected'")

    if body.status == "approved":
        if request.request_type == "startup_withdrawal":
            startup = db.query(Startup).filter(Startup.id == request.startup_id).first()
            if not startup or startup.withdrawable_balance < request.amount:
                 raise HTTPException(status_code=400, detail="Insufficient funds in startup balance at time of approval")
            startup.withdrawable_balance -= request.amount
        elif request.request_type == "investor_reclaim":
            investment = db.query(Investment).filter(Investment.id == request.investment_id).first()
            if not investment or investment.escrow_balance < request.amount:
                 raise HTTPException(status_code=400, detail="Insufficient funds in escrow at time of approval")
            investment.escrow_balance -= request.amount
            # The amount is reclaimed by investor, so total invested amount also decreases?
            # Usually yes, or it stays as 'total commitment' but here 'amount' is 'total invested USDC'.
            investment.amount -= request.amount

    request.status = body.status
    request.admin_feedback = body.admin_feedback
    db.commit()
    db.refresh(request)

    logger.info(f"Admin {current_user.id} reviewed withdrawal request {request_id}: {body.status}")
    return request
