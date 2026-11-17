from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from app.application.dto.schemas import ChatMessageDTO, PRLineDTO
from app.application.use_cases.chat_intake_use_case import ChatIntakeUseCase
from app.application.use_cases.process_batch_use_case import ProcessBatchUseCase
from app.presentation.api_v1.dependencies import get_chat_intake_use_case, get_process_batch_use_case

router = APIRouter(prefix="", tags=["Chat Intake"])

@router.post("/chat")
async def chat_intake(
    message: ChatMessageDTO,
    use_case: ChatIntakeUseCase = Depends(get_chat_intake_use_case)
):
    return use_case.execute(user_text=message.content, context=message.metadata)

@router.post("/pr/submit")
async def submit_single_pr(
    pr_data: PRLineDTO,
    process_use_case: ProcessBatchUseCase = Depends(get_process_batch_use_case)
):
    if not pr_data.pr_no:
        pr_data.pr_no = f"PR-CHAT-{int(datetime.utcnow().timestamp()) % 10000:04d}"
    if not pr_data.created_at:
        pr_data.created_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    result = process_use_case.execute(pr_dtos=[pr_data], filename="single_pr_chat.csv")
    decision = result.decisions[0]

    return {
        "status": "success",
        "pr": pr_data,
        "decision": decision
    }
