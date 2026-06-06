"""Connector registry — builds a live ``Connector`` from a stored configuration.

Maps a ``SourceType`` to its factory. Unimplemented sources raise
``ConnectorNotImplemented`` so the API can return a clear 422 rather than failing
deep in a sync.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.connectors import github
from app.connectors.base import Connector
from app.domain.enums import SourceType


class ConnectorNotImplemented(Exception):
    """Raised when a source type has no runnable connector yet."""


_FACTORIES = {
    SourceType.GITHUB: github.build,
}


def build_connector(
    source_type: SourceType,
    config: dict[str, Any],
    secret: str | None,
    client: httpx.AsyncClient,
) -> Connector:
    factory = _FACTORIES.get(source_type)
    if factory is None:
        raise ConnectorNotImplemented(
            f"Connector for '{source_type.value}' is not implemented yet"
        )
    return factory(config, secret, client)


def is_implemented(source_type: SourceType) -> bool:
    return source_type in _FACTORIES
