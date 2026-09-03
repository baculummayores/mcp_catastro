"""Pruebas de seguridad XML y ciclo de vida del cliente HTTP."""

import asyncio

import pytest

from mcp_server import app, app_lifespan
from services.catastro_service import CatastroService


def test_lifespan_reuses_and_closes_http_client() -> None:
    async def run() -> None:
        async with app_lifespan(app) as context:
            http_client = context.catastro_service.http_client

            assert context.ai_service.catastro_service is context.catastro_service
            assert context.ai_service.catastro_service.http_client is http_client
            assert http_client.is_closed is False

        assert http_client.is_closed is True

    asyncio.run(run())


def test_xml_parser_rejects_entities() -> None:
    async def run() -> None:
        malicious_xml = """<?xml version="1.0"?>
<!DOCTYPE data [<!ENTITY secret SYSTEM "file:///etc/passwd">]>
<data>&secret;</data>
"""
        service = CatastroService()

        try:
            with pytest.raises(ValueError, match="Error parseando respuesta"):
                service._parsear_respuesta_xml(malicious_xml)
        finally:
            await service.aclose()

    asyncio.run(run())
