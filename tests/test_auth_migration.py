from sqlalchemy import create_engine, inspect, text

from app.db.migrations import migrate_sqlite_user_email_nullable


def test_migration_preserves_local_users_and_allows_kakao_users(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'legacy.sqlite'}")
    with engine.begin() as connection:
        connection.execute(text(
            "CREATE TABLE user (idx INTEGER NOT NULL PRIMARY KEY, email VARCHAR NOT NULL, "
            "password VARCHAR NOT NULL, name VARCHAR NOT NULL)"
        ))
        connection.execute(text("CREATE UNIQUE INDEX ix_user_email ON user (email)"))
        connection.execute(text(
            "INSERT INTO user (idx, email, password, name) VALUES (7, 'local@example.com', 'hash', 'Local')"
        ))

    migrate_sqlite_user_email_nullable(engine)
    migrate_sqlite_user_email_nullable(engine)

    with engine.begin() as connection:
        row = connection.execute(text("SELECT idx, email, password, name FROM user")).one()
        connection.execute(text(
            "INSERT INTO user (idx, email, password, name) VALUES (8, NULL, 'generated', 'Kakao')"
        ))
        assert row == (7, "local@example.com", "hash", "Local")

    columns = {column["name"]: column for column in inspect(engine).get_columns("user")}
    indexes = {index["name"]: index for index in inspect(engine).get_indexes("user")}
    assert columns["email"]["nullable"]
    assert indexes["ix_user_email"]["unique"]
    engine.dispose()
