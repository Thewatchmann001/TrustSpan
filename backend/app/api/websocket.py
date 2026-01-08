"""
WebSocket Server for Real-time Chat
Handles WebSocket connections for live messaging
"""
from fastapi import WebSocket, WebSocketDisconnect, Depends
from typing import Dict, List
import json
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Message, Conversation, User
from app.utils.logger import logger


class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        # Store connections by conversation_id: {user_id: websocket}
        self.active_connections: Dict[int, Dict[int, WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, conversation_id: int, user_id: int):
        """Connect a user to a conversation"""
        await websocket.accept()
        
        if conversation_id not in self.active_connections:
            self.active_connections[conversation_id] = {}
        
        self.active_connections[conversation_id][user_id] = websocket
        logger.info(f"User {user_id} connected to conversation {conversation_id}")
    
    def disconnect(self, conversation_id: int, user_id: int):
        """Disconnect a user from a conversation"""
        if conversation_id in self.active_connections:
            if user_id in self.active_connections[conversation_id]:
                del self.active_connections[conversation_id][user_id]
                logger.info(f"User {user_id} disconnected from conversation {conversation_id}")
            
            # Clean up empty conversation
            if not self.active_connections[conversation_id]:
                del self.active_connections[conversation_id]
    
    async def send_personal_message(self, message: dict, conversation_id: int, user_id: int):
        """Send message to a specific user in a conversation"""
        if conversation_id in self.active_connections:
            if user_id in self.active_connections[conversation_id]:
                websocket = self.active_connections[conversation_id][user_id]
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {str(e)}")
    
    async def broadcast_to_conversation(self, message: dict, conversation_id: int, exclude_user_id: int = None):
        """Broadcast message to all users in a conversation"""
        if conversation_id in self.active_connections:
            disconnected_users = []
            for user_id, websocket in self.active_connections[conversation_id].items():
                if user_id != exclude_user_id:
                    try:
                        await websocket.send_json(message)
                    except Exception as e:
                        logger.error(f"Error broadcasting to user {user_id}: {str(e)}")
                        disconnected_users.append(user_id)
            
            # Clean up disconnected users
            for user_id in disconnected_users:
                self.disconnect(conversation_id, user_id)


manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, conversation_id: int, user_id: int):
    """WebSocket endpoint for real-time chat"""
    await manager.connect(websocket, conversation_id, user_id)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                
                # Handle different message types
                if message_data.get("type") == "ping":
                    # Respond to ping with pong
                    await websocket.send_json({"type": "pong"})
                elif message_data.get("type") == "typing":
                    # Broadcast typing indicator
                    await manager.broadcast_to_conversation(
                        {
                            "type": "typing",
                            "user_id": user_id,
                            "is_typing": message_data.get("is_typing", False)
                        },
                        conversation_id,
                        exclude_user_id=user_id
                    )
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received from user {user_id}")
                
    except WebSocketDisconnect:
        manager.disconnect(conversation_id, user_id)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {str(e)}")
        manager.disconnect(conversation_id, user_id)


async def notify_new_message(db: Session, message: Message, conversation_id: int):
    """Notify all connected users in a conversation about a new message"""
    try:
        # Get sender info
        sender = db.query(User).filter(User.id == message.sender_id).first()
        
        # Prepare message data
        message_data = {
            "type": "new_message",
            "message": {
                "id": message.id,
                "conversation_id": message.conversation_id,
                "sender_id": message.sender_id,
                "sender_name": sender.full_name if sender else "Unknown",
                "content": message.content,
                "read": message.read,
                "created_at": message.created_at.isoformat()
            }
        }
        
        # Broadcast to all connected users in the conversation
        await manager.broadcast_to_conversation(
            message_data,
            conversation_id,
            exclude_user_id=message.sender_id
        )
        
        logger.info(f"Notified conversation {conversation_id} about new message {message.id}")
    except Exception as e:
        logger.error(f"Error notifying about new message: {str(e)}")
