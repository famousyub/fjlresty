import enum
from datetime import datetime
from typing import Dict, List, Optional, TypeVar

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base

from configures.settings import date_format

Meta = declarative_base()
db = SQLAlchemy(model_class=Meta)

Column = db.Column
relationship = db.relationship

T = TypeVar('T', bound=db.Model)


class SurrogatePK:
    """A mixin that adds a surrogate integer 'primary key' column named ``id`` to any declarative-mapped class."""

    __table_args__ = {'extend_existing': True}

    id = Column(db.Integer, primary_key=True)

    @classmethod
    def get_by_id(cls, record_id) -> Optional[SQLAlchemy]:
        """Get record by ID."""
        if any(
            (
                isinstance(record_id, (str, bytes)) and record_id.isdigit(),
                isinstance(record_id, (int, float)),
            )
        ):
            return cls.query.get(int(record_id))
        return None


class Base(db.Model, SurrogatePK):
    """DataBase Model that Contains CRUD Operations"""

    __abstract__ = True

    @classmethod
    def parse_schema(cls, **kwargs) -> Dict:
        column_names = cls.__table__.columns.keys()
        for key in filter(lambda col_name: col_name not in column_names, kwargs.copy().keys()):
            kwargs.pop(key)

        return kwargs

    @classmethod
    def create(cls, commit=True, **kwargs):
        kwargs = cls.parse_schema(**kwargs)
        instance = cls(**kwargs)

        return instance.save(commit)

    @classmethod
    def create_many(cls, kwargs_list) -> List[T]:
        return [cls.create(**kwargs) for kwargs in kwargs_list]

    def update(self, commit=True, **kwargs):
        """Update specific fields of a record."""
        kwargs = self.parse_schema(**kwargs)
        for attr, value in kwargs.items():
            setattr(self, attr, value)
        return commit and self.save() or self

    def delete(self, commit=True):
        """Remove the record from the database."""
        db.session.delete(self)
        return commit and db.session.commit()

    def save(self, commit=True) -> T:
        """Save the record."""
        db.session.add(self)
        if commit:
            db.session.commit()
        return self

    def _to_json(self, value):
        if hasattr(value, 'as_dict'):
            return value.as_dict()
        elif isinstance(value, datetime):
            return value.strftime(date_format)
        elif isinstance(value, enum.Enum):
            return value.name
        elif isinstance(value, list):
            return [self._to_json(v) for v in value]
        elif isinstance(value, dict):
            return {k: self._to_json(v) for k, v in value.items()}
        else:
            return value

    def as_dict(self):
        column_names = self.__table__.columns.keys()
        return {c: self._to_json(getattr(self, c)) for c in column_names}


def reference_col(table_name, nullable=False, pk_name='id', **kwargs):
    """Column that adds primary key foreign key reference.

    Usage: ::

        category_id = reference_col('category')
        category = relationship('Category', backref='categories')
    """
    return Column(db.ForeignKey('{0}.{1}'.format(table_name, pk_name)), nullable=nullable, **kwargs)
