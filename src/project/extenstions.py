import meilisearch as _meili_lib
from flask_babel import Babel
from flask_caching import Cache
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
babel = Babel()
migrate = Migrate()
csrf = CSRFProtect()
cache = Cache()


class _MeiliSearch:
    def __init__(self):
        self._client = None

    def init_app(self, app) -> None:
        url = app.config.get("MEILI_URL", "https://search.arstan.page")
        key = app.config.get("MEILI_MASTER_KEY", "")
        self._client = _meili_lib.Client(url, key)

    @property
    def client(self) -> _meili_lib.Client:
        if self._client is None:
            raise RuntimeError("MeiliSearch not initialized. Call init_app first.")
        return self._client


meili = _MeiliSearch()
