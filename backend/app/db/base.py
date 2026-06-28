from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from app.investigations import models  # noqa: E402,F401
from app.source_data import models  # noqa: E402,F401
