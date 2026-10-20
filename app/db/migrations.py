from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def migrate_sqlite_user_email_nullable(engine: Engine) -> None:
    if engine.dialect.name != "sqlite" or not inspect(engine).has_table("user"):
        return

    columns = {column["name"]: column for column in inspect(engine).get_columns("user")}
    email = columns.get("email")
    if email is None or email["nullable"]:
        return

    required = {"idx", "email", "password", "name"}
    if not required.issubset(columns):
        raise RuntimeError("Cannot safely migrate user table: required columns are missing")

    with engine.begin() as connection:
        connection.execute(text(
            "CREATE TABLE user_new (idx INTEGER NOT NULL PRIMARY KEY, email VARCHAR, "
            "password VARCHAR NOT NULL, name VARCHAR NOT NULL)"
        ))
        connection.execute(text(
            "INSERT INTO user_new (idx, email, password, name) "
            "SELECT idx, email, password, name FROM user"
        ))
        connection.execute(text("DROP TABLE user"))
        connection.execute(text("ALTER TABLE user_new RENAME TO user"))
        connection.execute(text("CREATE UNIQUE INDEX ix_user_email ON user (email)"))


def migrate_sqlite_esg_report_page_count(engine: Engine) -> None:
    if engine.dialect.name != "sqlite" or not inspect(engine).has_table("esg_report"):
        return
    columns = {column["name"] for column in inspect(engine).get_columns("esg_report")}
    if "page_count" in columns:
        return
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE esg_report ADD COLUMN page_count INTEGER NULL"))
