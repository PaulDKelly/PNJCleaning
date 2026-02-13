from sqlmodel import Session, select
from app.database import engine
from app.models import User
from app.security import get_password_hash

def reset_password(username, new_password):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == username)).first()
        if user:
            print(f"Found user: {user.username}")
            user.password = get_password_hash(new_password)
            session.add(user)
            session.commit()
            print(f"Password for {username} updated successfully.")
        else:
            print(f"User {username} not found.")

if __name__ == "__main__":
    reset_password("pnj_admin", "pnj_p123")
