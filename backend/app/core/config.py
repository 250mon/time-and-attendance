from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = (
        "postgresql+psycopg://clinic_time_user:change_me@localhost:5432/clinic_time"
    )
    backend_secret_key: str = "change_me"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    cookie_secure: bool = False
    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"
    clinic_timezone: str = "Asia/Seoul"
    multi_tenant_enabled: bool = False
    clinic_bootstrap_secret: str = ""
    platform_admin_secret: str = ""
    seed_clinic_name: str = "Demo Clinic"
    seed_clinic_slug: str = "demo"
    seed_admin_email: str = "admin@clinic.example"
    seed_admin_password: str = "ChangeMe123!"
    seed_admin_name: str = "Clinic Admin"
    log_level: str = "INFO"

    # Annual leave accrual (LSA Art. 60 + fiscal-year bulk grant)
    leave_fiscal_start_month: int = 1
    leave_fiscal_start_day: int = 1
    leave_fiscal_rounding: str = "round_2"
    leave_adjustment_mode: str = "anniversary_top_up"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
