#!/usr/bin/env python3
"""Servidor MCP v2 para consultar el Catastro de España."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Annotated, Any, Literal

import httpx
from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from mcp.types import ToolAnnotations
from pydantic import Field

from config.settings import configure_logging, get_settings
from models.catastro_models import ReferenciaCatastral
from services.ai_summary import AIService
from services.catastro_service import CatastroService

logger = logging.getLogger(__name__)

settings = get_settings()


@dataclass(frozen=True)
class AppContext:
    """Recursos compartidos durante la vida del servidor MCP."""

    catastro_service: CatastroService
    ai_service: AIService


@asynccontextmanager
async def app_lifespan(server: MCPServer) -> AsyncIterator[AppContext]:
    """Crea una única conexión HTTP reutilizable y garantiza su cierre."""
    async with httpx.AsyncClient(timeout=settings.catastro_timeout) as http_client:
        catastro_service = CatastroService(http_client=http_client)
        yield AppContext(
            catastro_service=catastro_service,
            ai_service=AIService(catastro_service=catastro_service),
        )


EXTERNAL_READ_ONLY_TOOL = ToolAnnotations(
    read_only_hint=True,
    destructive_hint=False,
    idempotent_hint=True,
    open_world_hint=True,
)
LOCAL_READ_ONLY_TOOL = ToolAnnotations(
    read_only_hint=True,
    destructive_hint=False,
    idempotent_hint=True,
    open_world_hint=False,
)

app = MCPServer(
    "catastro-mcp",
    title="Catastro de España",
    description="Consultas de datos públicos del Catastro de España.",
    instructions=(
        "Usa las herramientas para consultar referencias catastrales, parcelas y "
        "coordenadas en España. La búsqueda por dirección es informativa porque "
        "la API pública del Catastro no la ofrece de forma fiable."
    ),
    version=settings.app_version,
    lifespan=app_lifespan,
)


def parse_direccion_completa(direccion: str) -> dict[str, Any]:
    """Descompone una dirección en los campos que espera el servicio."""
    try:
        partes = [parte.strip().upper() for parte in direccion.split(",")]
        if len(partes) < 3:
            return {
                "error": (
                    "Formato incorrecto. Use: 'TIPO_VIA NOMBRE_VIA NUMERO, "
                    "CODIGO_POSTAL, MUNICIPIO, PROVINCIA'"
                ),
                "direccion_original": direccion,
            }

        via_completa = partes[0]
        tipos_via = [
            "CALLE",
            "AVENIDA",
            "PLAZA",
            "PASEO",
            "CARRETERA",
            "CAMINO",
            "TRAVESIA",
            "GLORIETA",
            "CL",
            "AV",
            "PZ",
            "PS",
            "CR",
        ]
        abreviaturas = {
            "CL": "CALLE",
            "AV": "AVENIDA",
            "PZ": "PLAZA",
            "PS": "PASEO",
            "CR": "CARRETERA",
        }
        tipo_via = "CALLE"
        nombre_via = via_completa
        numero = ""

        for tipo in tipos_via:
            if via_completa.startswith(f"{tipo} "):
                tipo_via = abreviaturas.get(tipo, tipo)
                resto_via = via_completa[len(tipo) :].strip()
                palabras = resto_via.split()
                if palabras and palabras[-1].replace("-", "").replace("/", "").isalnum():
                    numero = palabras[-1]
                    nombre_via = " ".join(palabras[:-1])
                else:
                    nombre_via = resto_via
                break

        if tipo_via == "CALLE" and nombre_via == via_completa:
            palabras = via_completa.split()
            if palabras and palabras[-1].replace("-", "").replace("/", "").isalnum():
                numero = palabras[-1]
                nombre_via = " ".join(palabras[:-1])

        if len(partes) == 3:
            codigo_postal = ""
            municipio, provincia = partes[1:3]
        elif len(partes) == 4:
            codigo_postal, municipio, provincia = partes[1:4]
        else:
            codigo_postal = ""
            municipio, provincia = partes[-2:]

        return {
            "tipo_via": tipo_via,
            "nombre_via": nombre_via,
            "numero": numero,
            "codigo_postal": codigo_postal,
            "municipio": municipio,
            "provincia": provincia,
            "direccion_original": direccion,
            "parseado_correctamente": True,
        }
    except Exception as exc:
        return {
            "error": f"Error parseando dirección: {exc}",
            "direccion_original": direccion,
            "parseado_correctamente": False,
        }


@app.tool(title="Consultar inmueble por referencia", annotations=EXTERNAL_READ_ONLY_TOOL)
async def consultar_catastro_por_referencia(
    ctx: Context[AppContext],
    referencia: Annotated[
        str,
        Field(
            min_length=20,
            max_length=20,
            description="Referencia catastral completa de 20 caracteres alfanuméricos.",
        ),
    ],
) -> dict[str, Any]:
    """Consulta los datos de un inmueble por su referencia catastral completa."""
    resultado = (
        await ctx.request_context.lifespan_context.catastro_service.consultar_por_referencia(
            referencia
        )
    )
    return resultado.model_dump(mode="json")


@app.tool(title="Consultar inmueble por coordenadas", annotations=EXTERNAL_READ_ONLY_TOOL)
async def consultar_catastro_por_coordenadas(
    ctx: Context[AppContext],
    latitud: Annotated[
        float, Field(ge=-90.0, le=90.0, description="Latitud WGS84 en grados decimales.")
    ],
    longitud: Annotated[
        float,
        Field(ge=-180.0, le=180.0, description="Longitud WGS84 en grados decimales."),
    ],
) -> dict[str, Any]:
    """Localiza y consulta un inmueble a partir de coordenadas en España."""
    resultado = (
        await ctx.request_context.lifespan_context.catastro_service.consultar_por_coordenadas(
            latitud, longitud
        )
    )
    return resultado.model_dump(mode="json")


@app.tool(title="Generar resumen catastral", annotations=EXTERNAL_READ_ONLY_TOOL)
async def generar_resumen_ia(
    ctx: Context[AppContext],
    referencia: Annotated[
        str,
        Field(
            min_length=20,
            max_length=20,
            description="Referencia catastral completa de 20 caracteres.",
        ),
    ],
    usar_openai: Annotated[
        bool, Field(description="Usar OpenAI si existe una clave configurada.")
    ] = False,
    idioma: Annotated[
        Literal["es", "en", "ca"],
        Field(description="Idioma del resumen: español, inglés o catalán."),
    ] = "es",
) -> str:
    """Genera un resumen profesional de los datos catastrales."""
    return await ctx.request_context.lifespan_context.ai_service.generar_resumen(
        referencia, usar_openai, idioma
    )


@app.tool(title="Validar referencia catastral", annotations=LOCAL_READ_ONLY_TOOL)
def validar_referencia_catastral(
    referencia: Annotated[
        str,
        Field(
            min_length=1,
            description="Referencia completa de 20 caracteres o código de parcela de 14.",
        ),
    ],
) -> dict[str, Any]:
    """Valida y explica referencias catastrales completas y parciales."""
    analisis = ReferenciaCatastral.analizar_referencia_detallado(referencia)
    return {
        "referencia": referencia,
        "es_valida": analisis["es_valida"],
        "mensaje": analisis["mensaje"],
        "analisis_detallado": analisis,
    }


@app.tool(title="Información de búsqueda por dirección", annotations=LOCAL_READ_ONLY_TOOL)
async def buscar_catastro_por_direccion(
    ctx: Context[AppContext],
    direccion_completa: Annotated[
        str,
        Field(
            min_length=1,
            description="Dirección: TIPO_VIA NOMBRE NUMERO, CODIGO_POSTAL, MUNICIPIO, PROVINCIA.",
        ),
    ],
) -> dict[str, Any]:
    """Explica las limitaciones de la búsqueda postal y ofrece alternativas."""
    componentes = parse_direccion_completa(direccion_completa)
    if "error" in componentes:
        return {
            "error": True,
            "herramienta": "buscar_catastro_por_direccion",
            "mensaje": componentes["error"],
            "direccion_recibida": direccion_completa,
            "formato_correcto": "TIPO_VIA NOMBRE_VIA NUMERO, CODIGO_POSTAL, MUNICIPIO, PROVINCIA",
            "ejemplos": [
                "CALLE REYES CATOLICOS 6, 18100, ARMILLA, GRANADA",
                "AVENIDA CONSTITUCION 25, 14011, CORDOBA, CORDOBA",
            ],
        }

    resultado = await ctx.request_context.lifespan_context.catastro_service.buscar_por_direccion(
        provincia=componentes.get("provincia", ""),
        municipio=componentes.get("municipio", ""),
        tipo_via=componentes.get("tipo_via", "CALLE"),
        nombre_via=componentes.get("nombre_via", ""),
        numero=componentes.get("numero", ""),
        direccion_original=direccion_completa,
    )
    return resultado.model_dump(mode="json")


@app.tool(title="Consultar parcela", annotations=EXTERNAL_READ_ONLY_TOOL)
async def consultar_parcela_por_codigo(
    ctx: Context[AppContext],
    codigo_parcela: Annotated[
        str,
        Field(
            min_length=14,
            max_length=14,
            description="Código de parcela catastral de 14 caracteres.",
        ),
    ],
) -> dict[str, Any]:
    """Consulta todos los inmuebles asociados a una parcela catastral."""
    resultado = (
        await ctx.request_context.lifespan_context.catastro_service.consultar_parcela_por_codigo(
            codigo_parcela
        )
    )
    return resultado.model_dump(mode="json")


@app.resource(
    "catastro://api/info",
    name="informacion_api_catastro",
    title="Información de la API del Catastro",
    description="Endpoints, capacidades y ejemplos del servidor.",
    mime_type="application/json",
)
def informacion_api_catastro() -> dict[str, Any]:
    """Describe las capacidades del servidor Catastro MCP."""
    return {
        "version": settings.app_version,
        "sdk_mcp": "2.x",
        "description": "Servidor MCP para consultas al Catastro de España",
        "herramientas_disponibles": [
            "consultar_catastro_por_referencia",
            "consultar_catastro_por_coordenadas",
            "buscar_catastro_por_direccion",
            "generar_resumen_ia",
            "validar_referencia_catastral",
            "consultar_parcela_por_codigo",
        ],
        "importante": (
            "La búsqueda por dirección no está disponible de forma fiable en la "
            "API pública del Catastro. Use sede.catastro.gob.es."
        ),
        "ejemplos_funcionales": {
            "referencia_completa": "4228928VG4141K0001IZ",
            "referencia_parcial": "2314501EG1421S",
            "coordenadas": {"latitud": 40.4168, "longitud": -3.7038},
        },
    }


def main() -> None:
    """Ejecuta el servidor mediante el transporte stdio."""
    configure_logging(settings)
    logger.info("Iniciando Catastro MCP con el SDK v2")
    app.run(transport="stdio")


if __name__ == "__main__":
    main()
