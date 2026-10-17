from pydantic_settings import BaseSettings, SettingsConfigDict


class Configuracion(BaseSettings):
    """Configuración central de RioTiendas."""

    app_nombre: str = "RIOTIENDAS API"
    app_ambiente: str = "desarrollo"
    app_llave_secreta: str = "RIOTIENDAS_LLAVE_DEMO_2026_CAMBIAR_EN_PRODUCCION"
    app_algoritmo_jwt: str = "HS256"
    app_expiracion_token_minutos: int = 1440
    app_url_bd: str = "sqlite:///./riotiendas.db"
    cors_origenes: str = "http://localhost,https://localhost,capacitor://localhost"

    @property
    def lista_cors(self) -> list[str]:
        return [origen.strip() for origen in self.cors_origenes.split(",") if origen.strip()]

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")


configuracion = Configuracion()
