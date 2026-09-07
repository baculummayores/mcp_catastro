"""Pruebas de integración en memoria para el SDK MCP v2."""

import asyncio
import json

from mcp import Client

from mcp_server import app


def test_mcp_v2_tools_and_resource(monkeypatch) -> None:
    from services.catastro_service import CatastroService
    from tests.test_catastro_responses import fixture

    async def request(self, endpoint, params):
        name = (
            "municipalities"
            if endpoint.endswith("ObtenerMunicipios")
            else "streets" if endpoint.endswith("ObtenerCallejero") else "address"
        )
        return fixture(name)

    monkeypatch.setattr(CatastroService, "_request", request)

    async def run() -> None:
        async with Client(app) as client:
            listed = await client.list_tools()
            tools = {tool.name: tool for tool in listed.tools}

            assert set(tools) == {
                "consultar_catastro_por_referencia",
                "consultar_catastro_por_coordenadas",
                "generar_resumen_ia",
                "validar_referencia_catastral",
                "buscar_catastro_por_direccion",
                "consultar_parcela_por_codigo",
                "buscar_catastro_por_direccion",
            }
            assert (
                tools["consultar_parcela_por_codigo"].input_schema["properties"]["codigo_parcela"][
                    "maxLength"
                ]
                == 14
            )
            external_tools = {
                "consultar_catastro_por_referencia",
                "consultar_catastro_por_coordenadas",
                "generar_resumen_ia",
                "consultar_parcela_por_codigo",
                "buscar_catastro_por_direccion",
            }
            local_tools = {
                "validar_referencia_catastral",
            }
            for tool_name in external_tools | local_tools:
                annotations = tools[tool_name].annotations
                assert annotations.read_only_hint is True
                assert annotations.destructive_hint is False
                assert annotations.idempotent_hint is True
                assert annotations.open_world_hint is (tool_name in external_tools)
            assert all(tool.output_schema for tool in tools.values())

            result = await client.call_tool(
                "validar_referencia_catastral",
                {"referencia": "2314501EG1421S"},
            )
            assert result.is_error is False
            assert result.structured_content is not None
            assert result.structured_content["es_valida"] is True
            assert result.structured_content["analisis_detallado"]["longitud"] == 14

            address = await client.call_tool(
                "buscar_catastro_por_direccion",
                {"direccion_completa": "CALLE REYES CATOLICOS 6, ARMILLA, GRANADA"},
            )
            assert address.is_error is False
            assert address.structured_content["estado_consulta"] == "exitosa"
            assert address.structured_content["total_inmuebles"] == 22

            invalid = await client.call_tool(
                "consultar_parcela_por_codigo",
                {"codigo_parcela": "CORTO"},
            )
            assert invalid.is_error is True

            resources = await client.list_resources()
            assert [resource.uri for resource in resources.resources] == ["catastro://api/info"]
            resource = await client.read_resource("catastro://api/info")
            payload = json.loads(resource.contents[0].text)
            assert payload["sdk_mcp"] == "2.x"

    asyncio.run(run())
