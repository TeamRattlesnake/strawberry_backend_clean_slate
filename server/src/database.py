"""
Модуль с классом для общения с базой данных
"""

import datetime
from sqlalchemy import (
    create_engine,
    Table,
    Column,
    String,
    Integer,
    DateTime,
    MetaData,
    inspect,
    select,
    update,
    insert,
)
from models import GenerateResultInfo


class DBException(Exception):
    """
    Класс исключения, связанного с базой данных
    """

    pass


class Database:
    def __init__(self, user, password, database, port, host):
        self.database_uri = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"
        self.engine = create_engine(self.database_uri)

        self.meta = MetaData()

        self.generated_data = Table(
            "generated_data",
            self.meta,
            Column("id", Integer, primary_key=True, nullable=False),
            Column("user_id", Integer, primary_key=True, nullable=False),
            Column("method", String(1024), nullable=False),
            Column("query", String(3072), nullable=False),
            Column("text", String(3072), nullable=False),
            Column("rating", Integer, nullable=False, default=0),
            Column(
                "date",
                DateTime(timezone=True),
                default=datetime.datetime.utcnow,
                nullable=False,
            ),
        )

    def need_migration(self) -> bool:
        """
        Проверяет, нужна ли миграция
        """
        try:
            if not inspect(self.engine).has_table("generated_data"):
                return True
            return False
        except Exception as exc:
            raise DBException(f"Error in need_migration: {exc}") from exc

    def migrate(self):
        """
        Делает миграцию (создает таблицы)
        """
        try:
            self.meta.create_all(self.engine)
        except Exception as exc:
            raise DBException(f"Error in migrate: {exc}") from exc

    def add_generated_data(
        self, query: str, text: str, user_id: str, gen_method: str
    ) -> int:
        """
        Добавляет сгенерированный текст с нулевым рейтингом
        """
        try:
            with self.engine.connect() as connection:
                insert_query = insert(self.generated_data).values(
                    query=query, text=text, user_id=user_id, method=gen_method
                )
                connection.execute(insert_query)

                get_id_query = select(self.generated_data.c.id).where(
                    self.generated_data.c.text == text
                )
                text_id = int(connection.execute(get_id_query).fetchall()[0][0])

                return text_id
        except Exception as exc:
            raise DBException(f"Error in add_generated_data: {exc}") from exc

    def change_rating(self, text_id: int, new_score: int):
        """
        Ставит генерации оценку
        """
        try:
            with self.engine.connect() as connection:
                update_query = (
                    update(self.generated_data)
                    .where(self.generated_data.c.id == text_id)
                    .values(rating=new_score)
                )
                connection.execute(update_query)
        except Exception as exc:
            raise DBException(f"Error in change_rating: {exc}") from exc

    def get_users_texts(
        self, user_id: int, offset: int, limit: int
    ) -> list[GenerateResultInfo]:
        """
        Выбирает всю информацию о текстах, сгенерированных юзером
        """
        try:
            with self.engine.connect() as connection:
                select_query = select(self.generated_data).where(
                    self.generated_data.c.user_id == user_id
                )
                if limit:
                    select_query = select_query.limit(limit)
                if offset:
                    select_query = select_query.offset(offset)

                response = select_query.fetchall()
                result = []
                for row in response:
                    result += [
                        GenerateResultInfo(
                            post_id=response[0],
                            user_id=response[1],
                            method=response[2],
                            hint=response[3],
                            text=response[4],
                            rating=response[5],
                            date=response[6],
                        )
                    ]
                return result

        except Exception as exc:
            raise DBException(f"Error in get_users_texts: {exc}") from exc
