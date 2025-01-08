from sqlalchemy import desc

from ops.extensions import db
from lib.util_sqlalchemy import ResourceMixin


class Research(ResourceMixin, db.Model):
    __tablename__ = "researches"
    id = db.Column(db.Integer, primary_key=True)

    # Relationships.
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    user = db.relationship("User", viewonly=True)

    question = db.Column(db.String(2000), nullable=False)
    answer = db.Column(db.String(2000), nullable=False)

    @classmethod
    def latest(cls, limit):
        """
        Return the latest X facts.

        :type limit: int
        :return: SQLAlchemy result
        """
        return Research.query.order_by(desc(Research.created_on)).limit(limit).all()
