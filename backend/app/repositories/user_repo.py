from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.user import User, UserRole


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email.ilike(email)).first()

    def get_users_by_role(self, role: UserRole, include_inactive: bool = False) -> List[User]:
        query = self.db.query(User).filter(User.role == role)
        if not include_inactive:
            query = query.filter(User.is_active.is_(True))
        return query.order_by(User.full_name.asc()).all()

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user: User) -> User:
        self.db.commit()
        self.db.refresh(user)
        return user
