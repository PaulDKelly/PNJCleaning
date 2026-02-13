from sqlmodel import Session, select
from app.database import engine
from app.models import User

def list_users():
    with Session(engine) as session:
        users = session.exec(select(User)).all()
        for user in users:
            print(f"User: {user.username}, Email: {user.email}")

if __name__ == "__main__":
    list_users()
