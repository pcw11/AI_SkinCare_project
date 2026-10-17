import os
from dataclasses import dataclass


@dataclass(frozen=True)
class PostgresConfig:
    host: str = "localhost"
    port: int = 5432
    dbname: str = "mirrorme"
    user: str = "postgres"
    password: str = "postgres"
    sslmode: str = "prefer"

    @classmethod
    def from_env(cls) -> "PostgresConfig":
        return cls(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            dbname=os.getenv("POSTGRES_DB", "mirrorme"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            sslmode=os.getenv("POSTGRES_SSLMODE", "prefer"),
        )

    @property
    def dsn(self) -> str:
        return (
            f"host={self.host} "
            f"port={self.port} "
            f"dbname={self.dbname} "
            f"user={self.user} "
            f"password={self.password} "
            f"sslmode={self.sslmode}"
        )
