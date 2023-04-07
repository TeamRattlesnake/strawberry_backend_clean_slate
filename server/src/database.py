"""
Модуль с классом для общения с базой данных
"""

import datetime
from sqlalchemy import create_engine, Table, Column, String, Integer, DateTime, MetaData, inspect, select, update, insert


class DBException(Exception):
    """
    Класс исключения, связанного с базой данных
    """
    pass


class Database():

    def __init__(self, user, password, database, port, host):
        self.database_uri = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"
        self.engine = create_engine(self.database_uri)

        self.meta = MetaData()

        self.generated_data = Table(
            "generated_data",
            self.meta,
            Column("id", Integer, primary_key=True, nullable=False),
            Column("query", String, nullable=False),
            Column("text", String, nullable=False),
            Column("rating", Integer, nullable=False, default=0),
            Column("date", DateTime(timezone=True),
                   default=datetime.datetime.utcnow, nullable=False),
        )

    def need_migration(self) -> bool:
        try:
            if not inspect(self.engine).has_table("generated_data"):
                return True
            return False
        except Exception as exc:
            raise DBException(f"Error in need_migration: {exc}") from exc

    def migrate(self):
        try:
            self.meta.create_all(self.engine)
        except Exception as exc:
            raise DBException(f"Error in migrate: {exc}") from exc

    def add_generated_data(self, query: str, text: str,) -> int:
        try:
            with self.engine.connect() as connection:
                insert_query = insert(self.generated_data).values(
                    query=query, text=text)
                connection.execute(insert_query)

                get_id_query = select(self.generated_data.c.id).where(
                    self.generated_data.c.text == text)
                text_id = int(connection.execute(
                    get_id_query).fetchall()[0][0])

                return text_id
        except Exception as exc:
            raise DBException(f"Error in add_generated_data: {exc}") from exc

    def change_rating(self, text_id: int, score_delta: int):
        try:
            with self.engine.connect() as connection:
                get_rating_query = select(self.generated_data.c.rating).where(
                    self.generated_data.c.id == text_id)
                rating = int(connection.execute(
                    get_rating_query).fetchall()[0][0])

                update_query = update(self.generated_data).where(
                    self.generated_data.c.id == text_id).values(rating=rating+score_delta)
                connection.execute(update_query)
        except Exception as exc:
            raise DBException(f"Error in change_rating: {exc}") from exc
