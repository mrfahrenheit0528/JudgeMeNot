import bcrypt
from sqlalchemy.orm import Session
from core.database import SessionLocal
from models.all_models import User, Event, AuditLog

class AdminService:
    def get_all_users(self):
        db: Session = SessionLocal()
        try:
            return db.query(User).all()
        finally:
            db.close()

    def create_user(self, name, username, password, role):
        db: Session = SessionLocal()
        try:
            if db.query(User).filter(User.username == username).first():
                return False, "Username already exists."

            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

            new_user = User(
                name=name,
                username=username,
                password_hash=hashed,
                role=role,
                is_active=True
            )
            db.add(new_user)
            db.commit()
            return True, "User created successfully."
        except Exception as e:
            return False, str(e)
        finally:
            db.close()

    def update_user(self, user_id, name, username, role, password=None):
        db: Session = SessionLocal()
        try:
            user = db.query(User).get(user_id)
            if not user: return False, "User not found"
            
            user.name = name
            user.username = username
            user.role = role
            
            # Only update password if a new one is provided
            if password:
                salt = bcrypt.gensalt()
                user.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
                
            db.commit()
            return True, "User updated successfully."
        except Exception as e:
            return False, str(e)
        finally:
            db.close()

    def delete_user(self, user_id):
        db: Session = SessionLocal()
        try:
            user = db.query(User).get(user_id)
            if not user: return False, "User not found"
            db.delete(user)
            db.commit()
            return True, "User deleted successfully."
        except Exception as e:
            return False, str(e)
        finally:
            db.close()

    def get_all_events(self):
        db: Session = SessionLocal()
        try:
            return db.query(Event).all()
        finally:
            db.close()

    def create_event(self, name, event_type):
        db: Session = SessionLocal()
        try:
            new_event = Event(
                name=name,
                event_type=event_type, # 'Pageant' or 'QuizBee'
                status='Active'
            )
            db.add(new_event)
            db.commit()
            return True, "Event created successfully."
        except Exception as e:
            return False, str(e)
        finally:
            db.close()
    
    def get_all_judges(self):
        """Returns only users with role='Judge'"""
        db = SessionLocal()
        try:
            return db.query(User).filter(User.role == "Judge").all()
        finally:
            db.close()

    def get_security_logs(self):
        """Fetches all audit logs with the associated Username"""
        db: Session = SessionLocal()
        try:
            # Join AuditLog with User to get the username instead of just user_id
            return db.query(AuditLog).join(User).order_by(AuditLog.timestamp.desc()).all()
        finally:
            db.close()
