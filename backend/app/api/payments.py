"""
Stripe card payments: create checkout session and handle webhooks.
Investor pays via Stripe Checkout; webhook records Investment with tx_signature = stripe:cs_xxx.
"""
import json
import stripe
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.db.session import get_db
from app.db.models import User, Startup, Investment
from app.core.config import settings
from app.core.dependencies import get_current_user
from app.utils.logger import logger

router = APIRouter(prefix="/api/payments", tags=["payments"])


class CreateCheckoutRequest(BaseModel):
    startup_id: str  # Startup's public startup_id (string)
    amount_usd: float  # Amount in USD (e.g. 50.00)
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class ConfirmSessionRequest(BaseModel):
    session_id: str  # Stripe Checkout session id (cs_xxx)


@router.post("/create-checkout-session")
async def create_checkout_session(
    body: CreateCheckoutRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a Stripe Checkout session for an investment.
    Returns { "url": "...", "session_id": "..." }. Redirect the user to url to pay.
    """
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe is not configured",
        )
    if body.amount_usd < 1.0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Minimum amount is 1 USD",
        )
    startup = db.query(Startup).filter(Startup.startup_id == body.startup_id).first()
    if not startup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Startup {body.startup_id} not found",
        )
    stripe.api_key = settings.STRIPE_SECRET_KEY
    # Stripe replaces {CHECKOUT_SESSION_ID} in success_url with the real id
    success_url = (
        body.success_url
        or f"{settings.FRONTEND_URL}/investor-platform?payment=success&session_id={{CHECKOUT_SESSION_ID}}"
    )
    cancel_url = body.cancel_url or f"{settings.FRONTEND_URL}/investor-platform?payment=cancelled"
    amount_cents = int(round(body.amount_usd * 100))
    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"Investment in {startup.name}",
                            "description": f"TrustBridge investment · {startup.sector}",
                        },
                        "unit_amount": amount_cents,
                    },
                    "quantity": 1,
                }
            ],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "investor_id": str(current_user.id),
                "startup_id": body.startup_id,
                "startup_db_id": str(startup.id),
                "amount_usd": str(round(body.amount_usd, 2)),
            },
        )
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Payment provider error",
        )
    return {"url": session.url, "session_id": session.id}


def _record_stripe_investment(
    db: Session,
    session_id: str,
    investor_id: int,
    startup_db_id: int,
    amount: float,
) -> Optional[Investment]:
    """Create Investment for Stripe session if not already recorded. Idempotent."""
    existing = db.query(Investment).filter(
        Investment.tx_signature == f"stripe:{session_id}"
    ).first()
    if existing:
        return existing
    investor = db.query(User).filter(User.id == investor_id).first()
    startup = db.query(Startup).filter(Startup.id == startup_db_id).first()
    if not investor or not startup:
        return None
    investment = Investment(
        startup_id=startup.id,
        investor_id=investor_id,
        amount=amount,
        escrow_balance=amount,  # Deposit directly into escrow
        released_amount=0.0,
        tx_signature=f"stripe:{session_id}",
    )
    db.add(investment)
    db.commit()
    db.refresh(investment)
    logger.info(
        f"Stripe investment recorded: id={investment.id} investor={investor_id} "
        f"startup={startup.id} amount={amount}"
    )
    return investment


@router.post("/confirm-session")
async def confirm_checkout_session(
    body: ConfirmSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    After Stripe Checkout success redirect: confirm session and record investment if not
    already done (e.g. when webhook hasn't run yet, or local dev without Stripe CLI).
    Idempotent; safe to call multiple times.
    """
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe is not configured",
        )
    session_id = (body.session_id or "").strip()
    if not session_id or not session_id.startswith("cs_"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session_id",
        )
    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        session = stripe.checkout.Session.retrieve(
            session_id,
            expand=[],
        )
    except stripe.error.InvalidRequestError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Checkout session not found",
        )
    except stripe.error.StripeError as e:
        logger.error(f"Stripe retrieve error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Payment provider error",
        )
    if session.get("payment_status") != "paid":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment not completed",
        )
    metadata = session.get("metadata") or {}
    investor_id_str = metadata.get("investor_id")
    startup_db_id_str = metadata.get("startup_db_id")
    amount_str = metadata.get("amount_usd")
    if not all([investor_id_str, startup_db_id_str, amount_str]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session metadata",
        )
    try:
        inv_id = int(investor_id_str)
        startup_pk = int(startup_db_id_str)
        amount = float(amount_str)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session metadata",
        )
    if inv_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Session does not belong to this user",
        )
    investment = _record_stripe_investment(
        db, session_id, inv_id, startup_pk, amount
    )
    if not investment:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not record investment",
        )
    return {
        "success": True,
        "investment_id": investment.id,
        "amount": investment.amount,
        "startup_id": metadata.get("startup_id"),
    }


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Stripe webhook: on checkout.session.completed, create an Investment record.
    Configure in Stripe Dashboard: Events to send: checkout.session.completed.
    """
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Stripe not configured")
    stripe.api_key = settings.STRIPE_SECRET_KEY
    body = await request.body()
    sig = request.headers.get("stripe-signature", "")
    if not settings.STRIPE_WEBHOOK_SECRET:
        logger.warning("STRIPE_WEBHOOK_SECRET not set; webhook signature not verified")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON")
    else:
        try:
            payload = stripe.Webhook.construct_event(
                body, sig, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError as e:
            raise HTTPException(status_code=400, detail="Invalid signature")
    if payload.get("type") != "checkout.session.completed":
        return {"received": True}
    try:
        session = payload["data"]["object"]
    except (KeyError, TypeError):
        return {"received": True}
    metadata = session.get("metadata") or {}
    investor_id = metadata.get("investor_id")
    startup_id_str = metadata.get("startup_id")
    startup_db_id = metadata.get("startup_db_id")
    amount_usd = metadata.get("amount_usd")
    session_id = session.get("id", "")
    if not all([investor_id, startup_db_id, amount_usd]):
        logger.warning(f"Webhook missing metadata: {metadata}")
        return {"received": True}
    try:
        inv_id = int(investor_id)
        startup_pk = int(startup_db_id)
        amount = float(amount_usd)
    except (TypeError, ValueError):
        logger.warning(f"Webhook invalid metadata: {metadata}")
        return {"received": True}
    _record_stripe_investment(db, session_id, inv_id, startup_pk, amount)
    return {"received": True}
