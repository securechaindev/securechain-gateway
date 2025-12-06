from app.utils import JSONEncoder, OpenAPIManager, ProxyHandler


class ServiceContainer:
    instance: ServiceContainer | None = None
    json_encoder_obj: JSONEncoder | None = None
    proxy_handler_obj: ProxyHandler | None = None
    openapi_manager_obj: OpenAPIManager | None = None

    def __new__(cls) -> ServiceContainer:
        if cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance

    @property
    def json_encoder(self) -> JSONEncoder:
        if self.json_encoder_obj is None:
            self.json_encoder_obj = JSONEncoder()
        return self.json_encoder_obj

    @property
    def proxy_handler(self) -> ProxyHandler:
        if self.proxy_handler_obj is None:
            self.proxy_handler_obj = ProxyHandler()
        return self.proxy_handler_obj

    @property
    def openapi_manager(self) -> OpenAPIManager:
        if self.openapi_manager_obj is None:
            self.openapi_manager_obj = OpenAPIManager(
                title="Secure Chain API Gateway", version="1.1.0"
            )
        return self.openapi_manager_obj

    def reset(self) -> None:
        self.json_encoder_obj = None
        self.proxy_handler_obj = None
        self.openapi_manager_obj = None


def get_json_encoder() -> JSONEncoder:
    return ServiceContainer().json_encoder


def get_proxy_handler() -> ProxyHandler:
    return ServiceContainer().proxy_handler


def get_openapi_manager() -> OpenAPIManager:
    return ServiceContainer().openapi_manager
