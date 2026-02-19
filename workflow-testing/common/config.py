from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = Field(default="postgresql://user:password@db:5432/shared_db", alias="DATABASE_URL")
    kafka_bootstrap_servers: str = Field(default="localhost:9092", alias="KAFKA_BOOTSTRAP_SERVERS")
    kafka_consumer_group: str = Field(default="warehouse", alias="KAFKA_CONSUMER_GROUP")

    location_service_port: int = Field(default=5001, alias="LOCATION_SERVICE_PORT")
    product_service_port: int = Field(default=5002, alias="PRODUCT_SERVICE_PORT")
    order_service_port: int = Field(default=5003, alias="ORDER_SERVICE_PORT")
    warehouse_service_port: int = Field(default=5004, alias="WAREHOUSE_SERVICE_PORT")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
