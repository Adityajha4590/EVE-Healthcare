import json
from fastapi import APIRouter, Depends, Header, Request, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.dependencies import get_db
from app.schemas.webhook import WebhookPaymentPayload
from app.services.webhook import verify_signature, process_payment_webhook

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post(
    "/payments",
    summary="Receive payment outcome callback",
    status_code=200,
)
async def payment_webhook_endpoint(
    request: Request,
    x_webhook_signature: str = Header(None),
    db: Session = Depends(get_db),
):
    """
    Webhook endpoint to receive payment statuses from the gateway.
    Protected by HMAC SHA256 signature.
    """
    # 1. Read raw body
    raw_body = await request.body()
    
    # 2 & 3 & 4 & 5 & 6. Compute and verify HMAC signature
    if not verify_signature(raw_body, x_webhook_signature, settings.WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid signature")
        
    # 7 & 8. Parse JSON body into Pydantic model
    try:
        data = json.loads(raw_body)
        payload = WebhookPaymentPayload.model_validate(data)
    except Exception:
        # Malformed JSON or invalid schema
        raise HTTPException(status_code=422, detail="Invalid payload")

    # 9. Pass the validated payload to the existing webhook service
    return process_payment_webhook(db, payload)
