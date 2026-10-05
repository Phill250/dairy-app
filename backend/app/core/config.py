from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "development"  # set to "production" on the server

    database_url: str = "postgresql+psycopg2://dairy_user:dairy_pass@localhost:5432/dairy_db"
    cors_origins: str = "http://localhost:3000"
    allowed_hosts: str = "localhost,127.0.0.1,testserver"
    frontend_url: str = "http://localhost:3000"

    ml_model_path: str = "app/ml/milk_yield_model.pkl"
    ml_model_sha256: str = ""

    jwt_private_key_path: str = "keys/private.pem"
    jwt_public_key_path: str = "keys/public.pem"
    jwt_algorithm: str = "RS256"
    jwt_issuer: str = "smart-dairy-manager"
    jwt_audience: str = "smart-dairy-manager-clients"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    max_failed_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    password_reset_token_expire_minutes: int = 30

    # Email: if BREVO_API_KEY is set, mail goes out over HTTPS (works on hosts that block SMTP).
    # Otherwise, if SMTP_HOST is set, SMTP is used. Otherwise no mail is sent.
    brevo_api_key: str = ""
    email_from: str = ""  # sender address verified in Brevo
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def allowed_host_list(self) -> list[str]:
        return [h.strip() for h in self.allowed_hosts.split(",") if h.strip()]


settings = Settings()