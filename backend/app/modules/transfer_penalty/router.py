from fastapi import APIRouter, HTTPException

from app.db import connect
from app.modules.transfer_penalty import repository as repo
from app.modules.transfer_penalty import service
from app.modules.transfer_penalty.schemas import TransferRuleCreate, TransferRuleUpdate

router = APIRouter(tags=["transfer-penalty"])


def _to_http(e: Exception) -> HTTPException:
    if isinstance(e, service.RuleNotFound):
        return HTTPException(status_code=404, detail="规则不存在")
    if isinstance(e, service.RuleConflict):
        return HTTPException(status_code=409, detail=str(e))
    return HTTPException(status_code=400, detail=str(e))


@router.get("/transfer-rules")
def list_rules():
    conn = connect()
    try:
        return {"items": repo.list_all(conn)}
    finally:
        conn.close()


@router.post("/transfer-rules", status_code=201)
def create_rule(body: TransferRuleCreate):
    conn = connect()
    try:
        return service.create_rule(conn, body.from_line, body.to_line, body.amount, body.active)
    except (service.RuleConflict, ValueError) as e:
        raise _to_http(e)
    finally:
        conn.close()


@router.put("/transfer-rules/{rule_id}")
@router.patch("/transfer-rules/{rule_id}")
def update_rule(rule_id: int, body: TransferRuleUpdate):
    conn = connect()
    try:
        return service.update_rule(conn, rule_id, body.model_dump(exclude_none=True))
    except (service.RuleNotFound, service.RuleConflict, ValueError) as e:
        raise _to_http(e)
    finally:
        conn.close()


@router.post("/transfer-rules/{rule_id}/disable")
def disable_rule(rule_id: int):
    conn = connect()
    try:
        return service.disable_rule(conn, rule_id)
    except service.RuleNotFound as e:
        raise _to_http(e)
    finally:
        conn.close()
