import contextvars
from typing import Any, Callable, Mapping, Optional, Tuple, Union

import cachetools
import jinja2
import sqlalchemy as sa
from cachetools import keys as cache_keys

from internal.templates import wrapping
from internal.templates.wrapping import BASE_TEMPLATE_NAME
from models import Template
from utils.db_session import db_session_manager
from utils.utils import SingletonMeta


class DbLoader(jinja2.BaseLoader):
    """
    Подгрузка шаблонов из бд
    """

    with_base_template = contextvars.ContextVar("with_base_template", default=True)

    def __init__(self):
        self._cache = cachetools.TTLCache(maxsize=32, ttl=60)

    def get_template(self, slug: str) -> Template:
        key = cache_keys.hashkey(slug)
        if templ := self._cache.get(key):
            return templ
        return self._get_template(slug)

    def _get_template(self, slug: str) -> Optional[Template]:
        """
        Получение объекта шаблона из БД.
        """
        with db_session_manager() as session:
            templ_obj: Template = session.scalar(
                sa.select(Template).where(Template.slug == slug)
            )
            if templ_obj:
                session.expunge(templ_obj)
            return templ_obj

    def pre_load_template(self, template: Template):
        """
        Предварительная загрузка шаблона в кэш
        """
        key = cache_keys.hashkey(
            self, template.slug
        )  # те же аргументы, что и в функции get_template
        self._cache[key] = template

    def get_source(
        self, environment: jinja2.Environment, template: str
    ) -> Tuple[str, Optional[str], Optional[Callable[[], bool]]]:
        """
        Подгрузка шаблона средствами jinja.

        :raise jinja2.TemplateNotFound: При отсутствии шаблона в БД
        """
        templ_obj = self.get_template(template)
        if templ_obj is None:
            raise jinja2.TemplateNotFound(
                f'Template "{template}" not found in database'
            )
        content, name = templ_obj.content, templ_obj.slug

        if not self.with_base_template.get():
            if name != BASE_TEMPLATE_NAME:
                content = wrapping.unwrap_template(content)

        return content, name, lambda: False

    def _enable_base_template(self):
        self.with_base_template.set(True)

    def _disable_base_template(self):
        self.with_base_template.set(False)

    def clear_cache(self):
        self._cache.clear()


class TemplateEnvironment(jinja2.Environment, metaclass=SingletonMeta):
    loader: DbLoader

    def __init__(self):
        loader = DbLoader()

        super().__init__(cache_size=0, loader=loader)

    # noinspection PyMethodOverriding
    def get_template(
        self,
        name: Union[str, "Template"],
        parent: Optional[str] = None,
        globals: Optional[Mapping[str, Any]] = None,
        wrap_by_base_template: bool = True,
    ) -> jinja2.Template:
        if wrap_by_base_template:
            # noinspection PyProtectedMember
            self.loader._enable_base_template()
        else:
            # noinspection PyProtectedMember
            self.loader._disable_base_template()

        template = super().get_template(name, parent, globals)
        return template
