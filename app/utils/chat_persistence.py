"""
Chat persistence service for storing and retrieving chat history.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union
from sqlalchemy import select, update, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from uuid import uuid4
import uuid
from pydantic_core import to_jsonable_python
from pydantic_ai.messages import ModelMessagesTypeAdapter

from app.db.models.chat import Chat, ChatMessage
from app.utils.pii import redact_pii

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
        
        try:
            db.add(chat)
            await db.commit()
            await db.refresh(chat)
            logger.info(f"Created new chat session with provided ID: {session_id}")
            return session_id
        except IntegrityError:
            # Another request created the same session concurrently
            await db.rollback()
            existing_chat = await ChatPersistenceService.get_chat_by_session_id(db, session_id)
            if existing_chat is None:
                # The error was not caused by a duplicate session; re-raise for visibility
                raise

            # Optionally link the user_id if it was missing previously
            if user_id and not existing_chat.user_id:
                setattr(existing_chat, "user_id", user_id)
                setattr(existing_chat, "updated_at", datetime.now(timezone.utc))
                await db.commit()

            logger.info(
                "Session %s already exists; returning existing session instead of creating a new one",
                session_id,
            )
            return existing_chat.session_id

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
    async def save_message(
        db: AsyncSession,
        session_id: str,
        message_type: str,
        message_object: Dict[str, Any],
        history: Optional[List[Any]] = None
    ) -> bool:
        """
        Save a single message for a chat session.
        
        Args:
            db: Database session
            session_id: The session ID to save the message for
            message_type: Type of message ('user' or 'assistant')
            message_object: Dictionary containing the message content
            history: Optional raw message history from the agent (only for assistant messages)
                     This should be the result of to_jsonable_python(result.all_messages())
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # First, get the chat
            chat = await ChatPersistenceService.get_chat_by_session_id(db, session_id)
            if not chat:
                logger.error(f"Chat session {session_id} not found")
                return False
            
            # Defense-in-depth: redact user text fields before persisting
            sanitized_object = message_object
            try:
                if message_type == "user":
                    # Common shapes: {"content": str, ...} or {"query": str, ...}
                    if isinstance(sanitized_object, dict):
                        if "content" in sanitized_object and isinstance(sanitized_object["content"], str):
                            sanitized_object = dict(sanitized_object)
                            sanitized_object["content"] = redact_pii(sanitized_object["content"])  # type: ignore
                        if "query" in sanitized_object and isinstance(sanitized_object["query"], str):
                            sanitized_object = dict(sanitized_object)
                            sanitized_object["query"] = redact_pii(sanitized_object["query"])  # type: ignore
            except Exception:
                # Do not block persistence on redaction errors
                pass

            # Create message
            message = ChatMessage(
                chat_id=chat.id,
                message_id=str(uuid4()),
                message_type=message_type,
                message_object=to_jsonable_python(sanitized_object),
                history=history,
                timestamp=datetime.now(timezone.utc)
            )
            
            db.add(message)
            
            # Update the chat's updated_at timestamp
            # Use setattr to avoid strict SQLAlchemy typing complaints in some stubs
            setattr(chat, "updated_at", datetime.now(timezone.utc))  # type: ignore[attr-defined]
            
            await db.commit()
            logger.info(f"Saved {message_type} message for chat session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving message: {str(e)}")
            await db.rollback()
            return False
    
    @staticmethod
    async def load_history(db: AsyncSession, session_id: str) -> Optional[List]:
        """
        Load message history for a chat session.
        
        Args:
            db: Database session
            session_id: The session ID to load messages for
            
        Returns:
            List of model messages if found and valid, None otherwise
        """
        try:
            chat = await ChatPersistenceService.get_chat_by_session_id(db, session_id)
            if not chat:
                logger.warning(f"Chat session {session_id} not found when loading history")
                return None
            
            # Get the most recent assistant message with history
            query = select(ChatMessage).where(
                (ChatMessage.chat_id == chat.id) & 
                (ChatMessage.message_type == 'assistant') & 
                (ChatMessage.history.isnot(None))
            ).order_by(ChatMessage.timestamp.desc())
            
            result = await db.execute(query)
            message = result.scalars().first()
            
            if message is not None and message.history is not None:
                logger.info(f"Found message history for session {session_id}")
                # Convert history back to ModelMessage format using ModelMessagesTypeAdapter
                return ModelMessagesTypeAdapter.validate_python(message.history)
            
            logger.info(f"No message history found for session {session_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error loading message history: {str(e)}")
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
    
    @staticmethod
    async def get_chat_with_messages(db: AsyncSession, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a chat by session ID with all its messages loaded properly for async context.
        
        Args:
            db: Database session
            session_id: The session ID to look up
            
        Returns:
            Dictionary with 'chat' and 'messages' if found, None otherwise
        """
        try:
            # First get the chat
            chat_query = select(Chat).where(Chat.session_id == session_id)
            chat_result = await db.execute(chat_query)
            chat = chat_result.scalars().first()
            
            if not chat:
                logger.warning(f"Chat session {session_id} not found")
                return None
            
            # Then get all messages for this chat with a separate query
            messages_query = select(ChatMessage).where(ChatMessage.chat_id == chat.id).order_by(ChatMessage.timestamp)
            messages_result = await db.execute(messages_query)
            messages = messages_result.scalars().all()
            
            return {
                "chat": chat,
                "messages": messages
            }
            
        except Exception as e:
            logger.error(f"Error getting chat with messages: {str(e)}")
            return None
    
    @staticmethod
    async def save_messages(db: AsyncSession, session_id: str, messages: List[Any]) -> bool:
        """
        Save a list of messages to the database.
        
        Args:
            db: Database session
            session_id: The session ID to save messages for
            messages: List of ModelMessage objects to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # First, get the chat
            chat = await ChatPersistenceService.get_chat_by_session_id(db, session_id)
            if not chat:
                logger.error(f"Chat session {session_id} not found")
                return False
                
            # Convert messages to Python objects
            messages_as_python = to_jsonable_python(messages)
            
            # Save each message
            for i, message in enumerate(messages_as_python):
                if i % 2 == 0:  # Even indices are user messages
                    message_type = "user"
                    message_obj = {"query": message.get("content", "")}
                else:  # Odd indices are assistant messages
                    message_type = "assistant"
                    message_obj = {
                        "session_id": session_id,
                        "answer": message.get("content", ""),
                        "sources": [],  # You may want to extract this from the message
                        "confidence": 0.9,  # Default value
                        "retriever_type": "default",
                        "trace_id": str(uuid.uuid4())
                    }
                
                # Create message
                chat_message = ChatMessage(
                    chat_id=chat.id,
                    message_id=str(uuid4()),
                    message_type=message_type,
                    message_object=message_obj,
                    history=messages_as_python if message_type == "assistant" else None,
                    timestamp=datetime.now(timezone.utc)
                )
                db.add(chat_message)
            
            # Update the chat's updated_at timestamp
            # Use setattr to avoid strict SQLAlchemy typing complaints in some stubs
            setattr(chat, "updated_at", datetime.now(timezone.utc))  # type: ignore[attr-defined]
            
            await db.commit()
            logger.info(f"Saved {len(messages_as_python)} messages for chat session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving messages: {str(e)}")
            await db.rollback()
            return False
    
    @staticmethod
    async def load_messages(db: AsyncSession, session_id: str) -> Optional[List[Any]]:
        """
        Load message history for a chat session as ModelMessage objects.
        
        Args:
            db: Database session
            session_id: The session ID to load messages for
            
        Returns:
            List of model messages if found and valid, None otherwise
        """
        try:
            # Use the get_chat_with_messages method to get properly loaded messages
            chat_with_messages = await ChatPersistenceService.get_chat_with_messages(db, session_id)
            if not chat_with_messages:
                logger.warning(f"Chat session {session_id} not found")
                return None
                
            messages = chat_with_messages["messages"]
            
            # Find the most recent assistant message with history
            latest_history = None
            for msg in reversed(messages):
                if msg.message_type == 'assistant' and msg.history:
                    latest_history = msg.history
                    break
            
            if latest_history:
                # Convert history back to ModelMessage format
                return ModelMessagesTypeAdapter.validate_python(latest_history)
            
            # If no history found, return empty list
            logger.info(f"No message history found for session {session_id}")
            return []
            
        except Exception as e:
            logger.error(f"Error loading messages: {str(e)}")
            return None
        
    @staticmethod
    async def get_or_create_user(db: AsyncSession, user_id: str):
        """
        Retrieve or create a user.
        
        Args:
            db: Database session
            user_id: The user ID to retrieve or create
            
        Returns:
            The user object
        """
        try:
            # Check if the user already exists
            query = select(Chat).where(Chat.user_id == user_id)
            result = await db.execute(query)
            user = result.scalars().first()
            
            if user:
                logger.info(f"Retrieved existing user with ID: {user_id}")
                return user
            
            # If user doesn't exist, create a new one
            user = Chat(
                user_id=user_id,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            
            logger.info(f"Created new user with ID: {user_id}")
            return user
            
        except Exception as e:
            logger.error(f"Error retrieving or creating user: {str(e)}")
            return None

    @staticmethod
    async def get_or_create_session(db: AsyncSession, session_id: str, user_id: str):
        """
        Retrieve or create a session.
        
        Args:
            db: Database session
            session_id: The session ID to retrieve or create
            user_id: The user ID associated with the session
            
        Returns:
            The session ID that was provided or created
        """
        try:
            # Check if the session already exists
            query = select(Chat).where(Chat.session_id == session_id)
            result = await db.execute(query)
            chat = result.scalars().first()
            
            if chat:
                logger.info(f"Retrieved existing session with ID: {session_id}")
                return session_id
            
            # If session doesn't exist, create a new one
            session_id = str(uuid4())
            chat = Chat(
                session_id=session_id,
                user_id=user_id,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.add(chat)
            await db.commit()
            await db.refresh(chat)
            
            logger.info(f"Created new session with ID: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Error retrieving or creating session: {str(e)}")
            return None

    @staticmethod
    async def get_chat_history(db: AsyncSession, session_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve chat history for a session.
        
        Args:
            db: Database session
            session_id: The session ID to retrieve history for
            
        Returns:
            List of message dictionaries containing message_id, message_type, message_object, and timestamp
        """
        try:
            chat = await ChatPersistenceService.get_chat_by_session_id(db, session_id)
            if not chat:
                return []

            query = select(ChatMessage).where(ChatMessage.chat_id == chat.id).order_by(ChatMessage.timestamp)
            result = await db.execute(query)
            messages = result.scalars().all()

            return [
                {
                    "message_id": message.message_id,
                    "message_type": message.message_type,
                    "message_object": message.message_object,
                    "timestamp": message.timestamp.isoformat(),
                }
                for message in messages
            ]
        except Exception as e:
            logger.error(f"Error retrieving chat history: {e}")
            return []

    @staticmethod
    async def delete_chat(db: AsyncSession, session_id: str):
        """
        Delete a chat session and its associated messages.
        
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

            # Delete messages
            await db.execute(
                delete(ChatMessage).where(ChatMessage.chat_id == chat.id)
            )

            # Delete chat
            await db.execute(
                delete(Chat).where(Chat.id == chat.id)
            )

            await db.commit()
            logger.info(f"Deleted chat session {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting chat session: {e}")
            await db.rollback()
            return False

    @staticmethod
    async def cleanup_old_chats(db: AsyncSession, retention_days: int = 90) -> Dict[str, int]:
        """
        Delete chats and their messages older than the given retention period.

        Args:
            db: Database session
            retention_days: Age threshold in days (default 90)

        Returns:
            Dict with counts of deleted records: {"messages_deleted": int, "chats_deleted": int}
        """
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)

            # Subquery to select old chat ids
            old_chats_subq = select(Chat.id).where(Chat.updated_at < cutoff)

            # Delete messages belonging to old chats first (no DB-level ON DELETE CASCADE configured)
            messages_result = await db.execute(
                delete(ChatMessage).where(ChatMessage.chat_id.in_(old_chats_subq))
            )

            # Delete old chats
            chats_result = await db.execute(
                delete(Chat).where(Chat.updated_at < cutoff)
            )

            await db.commit()

            messages_deleted = messages_result.rowcount or 0
            chats_deleted = chats_result.rowcount or 0
            logger.info(
                f"Retention cleanup completed: deleted {messages_deleted} messages and {chats_deleted} chats older than {retention_days} days"
            )
            return {"messages_deleted": messages_deleted, "chats_deleted": chats_deleted}
        except Exception as e:
            logger.error(f"Error during retention cleanup: {e}")
            await db.rollback()
            return {"messages_deleted": 0, "chats_deleted": 0}
