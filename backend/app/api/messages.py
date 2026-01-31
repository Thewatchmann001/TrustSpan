"""
Chat/Messaging API
Handles conversations and messages between investors and startups
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os
import uuid
from pathlib import Path

from app.db.session import get_db
from app.db.models import Conversation, Message, User, Startup
from app.utils.logger import logger
from app.api.websocket import notify_new_message
from app.core.config import settings

router = APIRouter()


class MessageCreate(BaseModel):
    conversation_id: int
    sender_id: int
    content: str


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    sender_id: int
    sender_name: str
    content: str
    read: bool
    read_at: Optional[datetime] = None
    file_url: Optional[str] = None
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: int
    investor_id: int
    investor_name: str
    startup_id: int
    startup_name: str
    created_at: datetime
    updated_at: datetime
    last_message: Optional[MessageResponse] = None
    unread_count: int = 0

    class Config:
        from_attributes = True


@router.post("/api/conversations", response_model=ConversationResponse)
async def create_or_get_conversation(
    investor_id: int,
    startup_id: int,
    db: Session = Depends(get_db)
):
    """Create or get existing conversation between investor and startup"""
    try:
        # Check if conversation exists
        conversation = db.query(Conversation).filter(
            Conversation.investor_id == investor_id,
            Conversation.startup_id == startup_id
        ).first()
        
        if not conversation:
            # Verify investor and startup exist
            investor = db.query(User).filter(User.id == investor_id).first()
            startup = db.query(Startup).filter(Startup.id == startup_id).first()
            
            if not investor:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Investor {investor_id} not found"
                )
            if not startup:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Startup {startup_id} not found"
                )
            
            # Create new conversation
            conversation = Conversation(
                investor_id=investor_id,
                startup_id=startup_id
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            logger.info(f"Created conversation {conversation.id} between investor {investor_id} and startup {startup_id}")
        
        # Get last message and unread count
        last_message = db.query(Message).filter(
            Message.conversation_id == conversation.id
        ).order_by(Message.created_at.desc()).first()
        
        unread_count = db.query(Message).filter(
            Message.conversation_id == conversation.id,
            Message.read == False,
            Message.sender_id != investor_id  # Only count messages not from the investor
        ).count()
        
        # Build response
        investor = db.query(User).filter(User.id == conversation.investor_id).first()
        startup = db.query(Startup).filter(Startup.id == conversation.startup_id).first()
        
        last_message_response = None
        if last_message:
            sender = db.query(User).filter(User.id == last_message.sender_id).first()
            last_message_response = MessageResponse(
                id=last_message.id,
                conversation_id=last_message.conversation_id,
                sender_id=last_message.sender_id,
                sender_name=sender.full_name if sender else "Unknown",
                content=last_message.content,
                read=last_message.read,
                created_at=last_message.created_at
            )
        
        return ConversationResponse(
            id=conversation.id,
            investor_id=conversation.investor_id,
            investor_name=investor.full_name if investor else "Unknown",
            startup_id=conversation.startup_id,
            startup_name=startup.name if startup else "Unknown",
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            last_message=last_message_response,
            unread_count=unread_count
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating/getting conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create/get conversation: {str(e)}"
        )


@router.post("/api/messages", response_model=MessageResponse)
async def send_message(
    message_data: MessageCreate,
    db: Session = Depends(get_db)
):
    """Send a message in a conversation"""
    try:
        # Verify conversation exists
        conversation = db.query(Conversation).filter(
            Conversation.id == message_data.conversation_id
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {message_data.conversation_id} not found"
            )
        
        # Verify sender is part of the conversation
        if message_data.sender_id != conversation.investor_id:
            # Check if sender is the startup founder
            startup = db.query(Startup).filter(Startup.id == conversation.startup_id).first()
            if not startup or message_data.sender_id != startup.founder_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not part of this conversation"
                )
        
        # Create message
        message = Message(
            conversation_id=message_data.conversation_id,
            sender_id=message_data.sender_id,
            content=message_data.content
        )
        db.add(message)
        
        # Update conversation timestamp
        conversation.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(message)
        
        # Get sender info
        sender = db.query(User).filter(User.id == message_data.sender_id).first()
        
        # Notify via WebSocket
        try:
            await notify_new_message(db, message, message_data.conversation_id)
        except Exception as e:
            logger.error(f"Error notifying via WebSocket: {str(e)}")
        
        logger.info(f"Message {message.id} sent in conversation {message_data.conversation_id}")
        
        return MessageResponse(
            id=message.id,
            conversation_id=message.conversation_id,
            sender_id=message.sender_id,
            sender_name=sender.full_name if sender else "Unknown",
            content=message.content,
            read=message.read,
            read_at=message.read_at,
            file_url=message.file_url,
            file_name=message.file_name,
            file_type=message.file_type,
            file_size=message.file_size,
            created_at=message.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}"
        )


@router.get("/api/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """Get all messages in a conversation"""
    try:
        # Verify conversation exists
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found"
            )
        
        # Get messages
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.asc()).all()
        
        # Build response
        result = []
        for message in messages:
            sender = db.query(User).filter(User.id == message.sender_id).first()
            result.append(MessageResponse(
                id=message.id,
                conversation_id=message.conversation_id,
                sender_id=message.sender_id,
                sender_name=sender.full_name if sender else "Unknown",
                content=message.content,
                read=message.read,
                read_at=message.read_at,
                file_url=message.file_url,
                file_name=message.file_name,
                file_type=message.file_type,
                file_size=message.file_size,
                created_at=message.created_at
            ))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting messages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get messages: {str(e)}"
        )


@router.get("/api/conversations/user/{user_id}", response_model=List[ConversationResponse])
async def get_user_conversations(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get all conversations for a user (investor or startup founder)"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )
        
        # Get conversations where user is investor
        investor_conversations = db.query(Conversation).filter(
            Conversation.investor_id == user_id
        ).all()
        
        # Get conversations where user is startup founder
        startups = db.query(Startup).filter(Startup.founder_id == user_id).all()
        startup_ids = [s.id for s in startups]
        founder_conversations = db.query(Conversation).filter(
            Conversation.startup_id.in_(startup_ids)
        ).all()
        
        # Combine and deduplicate
        all_conversations = list(set(investor_conversations + founder_conversations))
        
        # Build response
        result = []
        for conversation in all_conversations:
            investor = db.query(User).filter(User.id == conversation.investor_id).first()
            startup = db.query(Startup).filter(Startup.id == conversation.startup_id).first()
            
            # Get last message
            last_message = db.query(Message).filter(
                Message.conversation_id == conversation.id
            ).order_by(Message.created_at.desc()).first()
            
            # Get unread count (messages not from this user)
            unread_count = db.query(Message).filter(
                Message.conversation_id == conversation.id,
                Message.read == False,
                Message.sender_id != user_id
            ).count()
            
            last_message_response = None
            if last_message:
                sender = db.query(User).filter(User.id == last_message.sender_id).first()
                last_message_response = MessageResponse(
                    id=last_message.id,
                    conversation_id=last_message.conversation_id,
                    sender_id=last_message.sender_id,
                    sender_name=sender.full_name if sender else "Unknown",
                    content=last_message.content,
                    read=last_message.read,
                    created_at=last_message.created_at
                )
            
            result.append(ConversationResponse(
                id=conversation.id,
                investor_id=conversation.investor_id,
                investor_name=investor.full_name if investor else "Unknown",
                startup_id=conversation.startup_id,
                startup_name=startup.name if startup else "Unknown",
                created_at=conversation.created_at,
                updated_at=conversation.updated_at,
                last_message=last_message_response,
                unread_count=unread_count
            ))
        
        # Sort by updated_at descending
        result.sort(key=lambda x: x.updated_at, reverse=True)
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user conversations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversations: {str(e)}"
        )


@router.put("/api/messages/{message_id}/read")
async def mark_message_read(
    message_id: int,
    db: Session = Depends(get_db)
):
    """Mark a message as read with timestamp"""
    try:
        message = db.query(Message).filter(Message.id == message_id).first()
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Message {message_id} not found"
            )
        
        if not message.read:
            message.read = True
            message.read_at = datetime.utcnow()
            db.commit()
        
        return {"success": True, "message_id": message_id, "read_at": message.read_at}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking message as read: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark message as read: {str(e)}"
        )


@router.put("/api/conversations/{conversation_id}/read-all")
async def mark_conversation_read(
    conversation_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Mark all messages in a conversation as read for a user"""
    try:
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found"
            )
        
        # Mark all unread messages not from this user as read
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.read == False,
            Message.sender_id != user_id
        ).all()
        
        for message in messages:
            message.read = True
        
        db.commit()
        
        return {"success": True, "conversation_id": conversation_id, "marked_count": len(messages)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking conversation as read: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark conversation as read: {str(e)}"
        )


@router.post("/api/messages/file-upload")
async def upload_file_message(
    file: UploadFile = File(...),
    conversation_id: int = Form(...),
    sender_id: int = Form(...),
    message_content: str = Form(""),
    db: Session = Depends(get_db)
):
    """Send a message with a file attachment"""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )
        
        # Validate file size (10MB max)
        contents = await file.read()
        file_size_mb = len(contents) / (1024 * 1024)
        if file_size_mb > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size ({file_size_mb:.2f}MB) exceeds maximum allowed size of 10MB"
            )
        
        # Validate file type
        allowed_extensions = {'.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.gif', '.webp'}
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type {file_extension} not allowed. Allowed types: PDF, DOC, DOCX, JPG, PNG, GIF, WEBP"
            )
        
        # Verify conversation exists
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found"
            )
        
        # Verify sender is part of the conversation
        if sender_id != conversation.investor_id:
            startup = db.query(Startup).filter(Startup.id == conversation.startup_id).first()
            if not startup or sender_id != startup.founder_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not part of this conversation"
                )
        
        # Create uploads directory if it doesn't exist
        from app.core.config import settings
        from pathlib import Path
        
        upload_base = Path(settings.UPLOAD_DIR)
        upload_dir = upload_base / "messages"
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = upload_dir / unique_filename
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Create message with file info
        file_url = f"/static/uploads/messages/{unique_filename}"
        message = Message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=message_content or f"Shared a file: {file.filename}",
            file_url=file_url,
            file_name=file.filename,
            file_type=file.content_type,
            file_size=len(contents)
        )
        db.add(message)
        
        # Update conversation timestamp
        conversation.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(message)
        
        # Get sender info
        sender = db.query(User).filter(User.id == sender_id).first()
        
        # Notify via WebSocket
        try:
            await notify_new_message(db, message, conversation_id)
        except Exception as e:
            logger.error(f"Error notifying via WebSocket: {str(e)}")
        
        logger.info(f"Message {message.id} with file attachment sent in conversation {conversation_id}")
        
        return MessageResponse(
            id=message.id,
            conversation_id=message.conversation_id,
            sender_id=message.sender_id,
            sender_name=sender.full_name if sender else "Unknown",
            content=message.content,
            read=message.read,
            read_at=message.read_at,
            file_url=message.file_url,
            file_name=message.file_name,
            file_type=message.file_type,
            file_size=message.file_size,
            created_at=message.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )


@router.get("/api/messages/file/{message_id}")
async def download_message_file(
    message_id: int,
    db: Session = Depends(get_db)
):
    """Download a file attached to a message"""
    try:
        # Get message
        message = db.query(Message).filter(Message.id == message_id).first()
        
        if not message or not message.file_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Extract filename from file_url
        # file_url format: /static/uploads/messages/{filename}
        filename = message.file_url.split('/')[-1]
        
        # Build file path
        upload_base = Path(settings.UPLOAD_DIR)
        file_path = upload_base / "messages" / filename
        
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found on server"
            )
        
        # Return file with proper headers
        return FileResponse(
            path=str(file_path),
            filename=message.file_name or filename,
            media_type=message.file_type or "application/octet-stream"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download file: {str(e)}"
        )
