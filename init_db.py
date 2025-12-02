import bcrypt
from sqlalchemy.orm import Session
from core.database import engine, Base, SessionLocal
from models.all_models import User, Event, Segment

def init_db():
    # 1. Create Tables
    print("⏳ Connecting to MySQL and creating tables...")
    try:
        # This checks your models and creates tables if they don't exist
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created successfully!")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return

    # 2. Open a Session
    db: Session = SessionLocal()

    # 3. Check if Admin exists (to prevent duplicates)
    existing_admin = db.query(User).filter(User.username == "admin").first()
    
    if not existing_admin:
        print("👤 Admin user not found. Creating one...")
        
        # IAS REQUIREMENT: Hash the password!
        # We use bcrypt to hash "admin123"
        password_raw = "admin123".encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password_raw, salt).decode('utf-8')

        admin_user = User(
            username="admin",
            password_hash=hashed_password,
            name="Super Admin",
            role="Admin",
            is_active=True,
            is_chairman=True # Can break ties
        )

        db.add(admin_user)
        db.commit()
        print("✅ Admin user created! (Username: admin / Pass: admin123)")
    else:
        print("ℹ️ Admin user already exists. Skipping creation.")

    db.close()
    print("🚀 Database initialization complete.")

if __name__ == "__main__":
    init_db()