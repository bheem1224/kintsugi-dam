import logging
from fastapi import APIRouter, Request, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import hmac
import hashlib
from ..core.config import settings
from ..core.database import get_db
from ..core.models import User

router = APIRouter()
logger = logging.getLogger(__name__)

# To use Verifier, paddle_billing expects a Request object that conforms to its protocol.
# FastApi Request doesn't directly conform to Paddle's Request interface exactly,
# so we might need a custom wrapper class for Verifier to consume it, OR we just build it out:
class PaddleRequestWrapper:
    def __init__(self, headers: dict, body: str):
        self.headers = headers
        self.body = body

@router.post("/paddle-webhook")
async def paddle_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    if not settings.PADDLE_WEBHOOK_SECRET:
        logger.error("PADDLE_WEBHOOK_SECRET is not configured.")
        raise HTTPException(status_code=500, detail="Webhook integration not configured.")

    body = await request.body()
    body_str = body.decode('utf-8')
    headers = {k: v for k, v in request.headers.items()}

    paddle_signature = request.headers.get("Paddle-Signature")
    if not paddle_signature:
        logger.error("Missing Paddle-Signature header")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing signature")

    parts = dict(part.split("=") for part in paddle_signature.split(";"))
    ts = parts.get("ts")
    h1 = parts.get("h1")

    if not ts or not h1:
        logger.error("Invalid Paddle-Signature format")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature format")

    payload = f"{ts}:{body_str}"

    expected_mac = hmac.new(
        settings.PADDLE_WEBHOOK_SECRET.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(h1, expected_mac):
        logger.error("Paddle webhook signature mismatch")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    # Parse JSON payload
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event_type = payload.get('event_type')
    if not event_type:
        return {"status": "ignored"}

    logger.info(f"Received Paddle webhook event: {event_type}")

    data = payload.get('data', {})

    if event_type in ['transaction.completed', 'subscription.created']:
        custom_data = data.get('custom_data') or {}
        user_id_str = custom_data.get('user_id')

        if not user_id_str:
            logger.warning(f"Paddle webhook {event_type} received with no user_id in custom_data. Ignoring.")
            return {"status": "ok", "message": "No user_id provided"}

        # ProUpsellModal sends the username as user_id to avoid leaking numeric IDs or if it's not available
        result = await db.execute(select(User).where(User.username == user_id_str))
        user = result.scalars().first()

        if user:
            user.is_pro = True

            customer_id = data.get('customer_id')
            if customer_id:
                user.paddle_customer_id = customer_id

            # If subscription.created, there is an ID
            # If transaction.completed, it might contain a subscription_id
            subscription_id = data.get('subscription_id')
            if not subscription_id and event_type == 'subscription.created':
                subscription_id = data.get('id')

            if subscription_id:
                user.paddle_subscription_id = subscription_id

            await db.commit()
            logger.info(f"User {user.username} upgraded to Pro via Paddle webhook.")
        else:
            logger.warning(f"Paddle webhook could not find user with id {user_id}")

    return {"status": "ok"}
