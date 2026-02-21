from app.db.database import SessionLocal, init_db
from app.models.user import User
from app.core.auth import hash_password

# Initialize DB (create tables if not exist)
init_db()

db = SessionLocal()
try:
    email = "test@example.com"
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        print(f"User {email} already exists")
    else:
        user = User(
            email=email,
            hashed_password=hash_password("password123"),
            full_name="Test User"
        )
        db.add(user)
        db.commit()
        print(f"User {email} created successfully")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
