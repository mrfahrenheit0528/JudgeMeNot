import bcrypt
from sqlalchemy.orm import Session
from models.all_models import User
from core.database import SessionLocal

class AuthService:
    def login(self, username, password):
        """
        Verifies credentials. 
        Returns: The User object if successful, None if failed.
        """
        db: Session = SessionLocal()
        try:
            # 1. Find the user
            user = db.query(User).filter(User.username == username).first()
            
            if not user:
                return None
            
            # 2. Check Password (using bcrypt)
            # Encode strings to bytes for bcrypt
            if bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
                if not user.is_active:
                    return "DISABLED" # Account is banned/inactive
                return user
            else:
                return None
        except Exception as e:
            print(f"Login Error: {e}")
            return None
        finally:
            db.close()

    def get_user_by_id(self, user_id):
        """Helper to retrieve user details during session check"""
        db = SessionLocal()
        try:
            return db.query(User).filter(User.id == user_id).first()
        finally:
            db.close()