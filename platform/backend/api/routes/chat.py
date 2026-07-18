from fastapi import APIRouter

from backend.schemas.models import ChatRequest, ChatResponse
from backend.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])
_service = ChatService()


@router.post("", response_model=ChatResponse)
def ask(request: ChatRequest):
    return _service.ask(request.question)
