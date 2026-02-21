import sys
import traceback
from app.db.database import SessionLocal, init_db
from app.models.user import User
from app.core.auth import hash_password

def test():
    try:
        init_db()
        db = SessionLocal()
        existing = db.query(User).filter(User.email == "test@test.com").first()
        user = User(
            email="test2@test.com",
            hashed_password=hash_password("password"),
            full_name="Test",
        )
        db.add(user)
        db.commit()
        print("Success")
    except Exception as e:
        traceback.print_exc()

if __name__ == "__main__":
    test()
