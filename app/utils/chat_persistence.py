"""
Chat persistence service for storing and retrieving chat history.
"""

import logging
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from pydantic_core import to_jsonable_python
from pydantic_ai.messages import ModelMessagesTypeAdapter

from app.db.models.chat import Chat, ChatMessage

logger = logging.getLogger(__name__)


class ChatPersistenceService:
    """Service for storing and retrieving chat history."""
    @staticmethod
    async def create_chat_session(db: AsyncSession, user_id: Optional[str] = None) -> str:
        """
        Create a new chat session.
        
        Args:
            db: Database session
            user_id: Optional user identifier
            
        Returns:
            The session ID for the new chat
        """
        # Generate a unique session ID
        session_id = str(uuid4())
        
        # Create chat record
        chat = Chat(
            session_id=session_id,
            user_id=user_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        db.add(chat)
        await db.commit()
        await db.refresh(chat)
        
        logger.info(f"Created new chat session with ID: {session_id}")
        return session_id
        
    @staticmethod
    async def create_chat_session_with_id(db: AsyncSession, session_id: str, user_id: Optional[str] = None) -> str:
        """
        Create a new chat session with a specific session ID.
        
        Args:
            db: Database session
            session_id: The session ID to use
            user_id: Optional user identifier
            
        Returns:
            The session ID that was provided
        """
        # Create chat record with the provided session ID
        chat = Chat(
            session_id=session_id,
            user_id=user_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        db.add(chat)
        await db.commit()
        await db.refresh(chat)
        
        logger.info(f"Created new chat session with provided ID: {session_id}")
        return session_id

    @staticmethod
    async def create_chat_session_with_id(db: AsyncSession, session_id: str, user_id: Optional[str] = None) -> str:
        """
        Create a new chat session with a specific session ID.
        
        Args:
            db: Database session
            session_id: The session ID to use
            user_id: Optional user identifier
            
        Returns:
            The session ID that was provided
        """
        # Create chat record with the provided session ID
        chat = Chat(
            session_id=session_id,
            user_id=user_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        db.add(chat)
        await db.commit()
        await db.refresh(chat)
        
        logger.info(f"Created new chat session with provided ID: {session_id}")
        return session_id

    @staticmethod
    async def get_chat_by_session_id(db: AsyncSession, session_id: str) -> Optional[Chat]:
        """
        Retrieve a chat by its session ID.
        
        Args:
            db: Database session
            session_id: The session ID to look up
            
        Returns:
            The chat object if found, None otherwise
        """
        query = select(Chat).where(Chat.session_id == session_id)
        result = await db.execute(query)
        chat = result.scalars().first()
        
        return chat

    @staticmethod
    async def save_messages(
        db: AsyncSession, 
        session_id: str, 
        messages: List[Any],
        append: bool = True
    ) -> bool:
        """
        Save messages for a chat session.
        
        Args:
            db: Database session
            session_id: The session ID to save messages for
            messages: List of ModelMessage objects from pydantic_ai
            append: Whether to append to existing messages or replace them
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # First, get the chat
            chat = await ChatPersistenceService.get_chat_by_session_id(db, session_id)
            if not chat:
                logger.error(f"Chat session {session_id} not found")
                return False
            
            # If not appending, delete existing messages
            if not append:
                query = select(ChatMessage).where(ChatMessage.chat_id == chat.id)
                result = await db.execute(query)
                existing_messages = result.scalars().all()
                for message in existing_messages:
                    await db.delete(message)
            
            # Get the current max message_idx
            query = select(ChatMessage).where(ChatMessage.chat_id == chat.id).order_by(ChatMessage.message_idx.desc())
            result = await db.execute(query)
            last_message = result.scalars().first()
            next_idx = (last_message.message_idx + 1) if last_message else 0
            
            # Convert PydanticAI messages to serializable format
            serializable_messages = to_jsonable_python(messages)
            
            # Store each message
            for msg_idx, message in enumerate(serializable_messages, start=next_idx):
                kind = message.get("kind")
                parts = message.get("parts", [])
                
                # Process each part of the message
                for part in parts:
                    part_kind = part.get("part_kind")
                      # Create a new message record
                    chat_message = ChatMessage(
                        chat_id=chat.id,
                        message_type=f"{kind}-{part_kind}" if part_kind else kind,
                        content=json.dumps(part),
                        model_name=message.get("model_name") if kind == "response" else None,
                        timestamp=datetime.fromisoformat(part.get("timestamp")) if part.get("timestamp") else datetime.now(timezone.utc),
                        meta_data={
                            "usage": message.get("usage") if kind == "response" else None,
                            "instructions": message.get("instructions") if kind == "request" else None
                        },
                        message_idx=msg_idx
                    )
                    
                    db.add(chat_message)
            
            # Update the chat's updated_at timestamp
            chat.updated_at = datetime.now(timezone.utc)
            
            await db.commit()
            logger.info(f"Saved {len(serializable_messages)} messages for chat session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving messages: {str(e)}")
            await db.rollback()
            return False    
    @staticmethod
    async def load_messages(db: AsyncSession, session_id: str) -> Optional[List]:
        """
        This method has been disabled to prevent loading message history.
        It now returns None to ensure no message history is loaded.
        
        Args:
            db: Database session
            session_id: The session ID to load messages for
            
        Returns:
            None - message history loading is disabled
        """
        logger.info(f"Message history loading has been disabled for session: {session_id}")
        return None
    @staticmethod
    async def delete_chat_session(db: AsyncSession, session_id: str) -> bool:
        """
        Delete a chat session and all its messages.
        
        Args:
            db: Database session
            session_id: The session ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            chat = await ChatPersistenceService.get_chat_by_session_id(db, session_id)
            if not chat:
                logger.error(f"Chat session {session_id} not found")
                return False
            
            await db.delete(chat)
            await db.commit()
            
            logger.info(f"Deleted chat session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting chat session: {str(e)}")
            await db.rollback()
            return False
