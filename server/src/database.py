"""
Модуль с классом для общения с базой данных
"""

from sqlalchemy import (
    create_engine,
    Table,
    Column,
    String,
    Integer,
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
    """
    Класс с логикой для взаимодействия с базой данных MariaDB/MySQL
    """

    def __init__(self, user, password, database, port, host):
        self.database_uri = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"
        self.engine = create_engine(self.database_uri)

        self.meta = MetaData()

        self.generated_data = Table(
            "generated_data",
            self.meta,
            Column(
                "id",
                Integer,
                primary_key=True,
                nullable=False,
                autoincrement=True,
            ),
            Column("user_id", Integer, nullable=False),
            Column("method", String(128), nullable=False),
            Column("query", String(4096), nullable=False),
            Column(
                "text",
                String(4096),
                nullable=False,
                default="",
            ),
            Column("rating", Integer, nullable=False),
            Column("unix_date", Integer, nullable=False),
            Column("group_id", Integer, nullable=False),
            Column("status", Integer, nullable=False),
            Column(
                "gen_time",
                Integer,
                nullable=False,
                default=0,
            ),
            Column("platform", String(128), nullable=False),
            Column("published", Integer, nullable=False),
            Column("hidden", Integer, nullable=False),
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

    def add_record(
        self,
        query: str,
        user_id: str,
        gen_method: str,
        group_id: int,
        unix_date: int,
        platform: str,
    ) -> int:
        """
        Добавляет запись о генерации, пока без результата, возвращает айди только что добавленной записи
        """
        try:
            with self.engine.connect() as connection:
                insert_query = insert(self.generated_data).values(
                    query=query,
                    user_id=user_id,
                    method=gen_method,
                    group_id=group_id,
                    unix_date=unix_date,
                    status=0,
                    rating=0,
                    platform=platform,
                    published=0,
                    hidden=0,
                )
                connection.execute(insert_query)

                get_id_query = select(self.generated_data.c.id).where(
                    (self.generated_data.c.query == query)
                    & (self.generated_data.c.unix_date == unix_date)
                )

                text_id = int(connection.execute(get_id_query).fetchall()[0][0])

                return text_id
        except Exception as exc:
            raise DBException(f"Error in add_record: {exc}") from exc

    def add_record_result(
        self,
        text_id: int,
        text: str,
        gen_time: int,
        is_ok: bool = True,
    ):
        """
        Добавляет в запись результат генерации и потраченное время
        """
        try:
            status = 1 if is_ok else 2
            with self.engine.connect() as connection:
                update_query = (
                    update(self.generated_data)
                    .where(self.generated_data.c.id == text_id)
                    .values(
                        text=text,
                        gen_time=gen_time,
                        status=status,
                    )
                )
                connection.execute(update_query)
        except Exception as exc:
            raise DBException(f"Error in add_record_result: {exc}") from exc

    def write_feedback(self, text_id: int, new_score: int):
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
            raise DBException(f"Error in write_feedback: {exc}") from exc

    def hide_generation(self, text_id: int, hidden=1):
        """
        Прячет (и открывает) пост и он не отправляется больше в истории
        """
        try:
            with self.engine.connect() as connection:
                update_query = (
                    update(self.generated_data)
                    .where(self.generated_data.c.id == text_id)
                    .values(hidden=hidden)
                )

                connection.execute(update_query)
        except Exception as exc:
            raise DBException(f"Error in hide_generation: {exc}") from exc

    def write_published(self, text_id: int):
        """
        Ставит генерации оценку
        """
        try:
            with self.engine.connect() as connection:
                update_query = (
                    update(self.generated_data)
                    .where(self.generated_data.c.id == text_id)
                    .values(published=1)
                )

                connection.execute(update_query)
        except Exception as exc:
            raise DBException(f"Error in write_published: {exc}") from exc

    def get_users_texts(
        self,
        group_id: int,
        user_id: int,
    ) -> list[GenerateResultInfo]:
        """
        Выбирает всю информацию о текстах, сгенерированных юзером
        """
        try:
            with self.engine.connect() as connection:
                if group_id:
                    select_query = (
                        select(self.generated_data)
                        .where(
                            (self.generated_data.c.user_id == user_id)
                            & (self.generated_data.c.group_id == group_id)
                            & (self.generated_data.c.status == 1)
                            & (self.generated_data.c.hidden == 0)
                        )
                        .order_by(self.generated_data.c.id.desc())
                    )
                else:
                    select_query = (
                        select(self.generated_data)
                        .where(
                            (self.generated_data.c.user_id == user_id)
                            & (self.generated_data.c.status == 1)
                            & (self.generated_data.c.hidden == 0)
                        )
                        .order_by(self.generated_data.c.id.desc())
                    )

                response = connection.execute(select_query).fetchall()

                result = []
                for row in response:
                    result += [
                        GenerateResultInfo(
                            post_id=row[0],
                            user_id=row[1],
                            method=row[2],
                            hint=row[3],
                            text=row[4],
                            rating=row[5],
                            date=row[6],
                            group_id=row[7],
                            status=row[8],
                            gen_time=row[9],
                            platform=row[10],
                            published=row[11],
                            hidden=row[12],
                        )
                    ]
                return result

        except Exception as exc:
            raise DBException(f"Error in get_users_texts: {exc}") from exc

    def get_status(self, text_id: int) -> str:
        """
        Получает статус генерации
        """
        try:
            with self.engine.connect() as connection:
                get_status_query = select(self.generated_data.c.status).where(
                    self.generated_data.c.id == text_id
                )
                status = int(connection.execute(get_status_query).fetchall()[0][0])

                return status
        except Exception as exc:
            raise DBException(f"Error in get_status: {exc}") from exc

    def get_value(self, text_id) -> str:
        """
        Получает результат генерации
        """
        try:
            with self.engine.connect() as connection:
                get_text_query = select(self.generated_data.c.text).where(
                    self.generated_data.c.id == text_id
                )
                text = str(connection.execute(get_text_query).fetchall()[0][0])

                return text
        except Exception as exc:
            raise DBException(f"Error in get_value: {exc}") from exc

    def user_owns_post(self, user_id: int, text_id: int) -> bool:
        """
        Проверяет, принадлежит ли пост пользователю
        """
        try:
            with self.engine.connect() as connection:
                select_query = select(self.generated_data.c.user_id).where(
                    self.generated_data.c.id == text_id
                )
                try:
                    user_id_db = int(connection.execute(select_query).fetchall()[0][0])
                except IndexError:
                    user_id_db = -1
                return user_id == user_id_db
        except Exception as exc:
            raise DBException(f"Error in user_owns_post: {exc}") from exc
