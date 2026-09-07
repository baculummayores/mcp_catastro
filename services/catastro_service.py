"""Consultas públicas al Catastro y normalización de sus respuestas WCF/ASMX."""

import asyncio
import json
import logging
import re
import time
from typing import Any, Dict

import httpx
from defusedxml import ElementTree as ET
from defusedxml.common import DefusedXmlException
from pydantic import ValidationError

from config.settings import (
    ERROR_MESSAGES,
    CatastroEndpoints,
    get_settings,
    log_failure,
    log_sensitive,
)
from models.catastro_models import (
    CatastroResponse,
    ConstruccionCatastral,
    Coordenadas,
    DatosBasicosInmueble,
    DireccionCatastral,
    InmuebleCatastral,
    ReferenciaCatastral,
)

logger = logging.getLogger(__name__)


def as_list(value: Any) -> list:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def number(value: Any) -> float | None:
    """Catastro usa punto de miles y coma decimal en los listados."""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if re.fullmatch(r"-?[0-9]{1,3}(?:\.[0-9]{3})+(?:,[0-9]+)?", text):
        text = text.replace(".", "")
    return float(text.replace(",", "."))


class CatastroService:
    def __init__(self, http_client: httpx.AsyncClient | None = None):
        self.settings = get_settings()
        self.base_url = self.settings.catastro_base_url
        self.timeout = self.settings.catastro_timeout
        self.max_retries = self.settings.catastro_max_retries
        self.retry_delay = self.settings.catastro_retry_delay
        self.http_client = http_client or httpx.AsyncClient(timeout=self.timeout)
        self._owns_http_client = http_client is None

    async def aclose(self) -> None:
        if self._owns_http_client:
            await self.http_client.aclose()

    def _error(self, referencia: str, exc: Exception) -> CatastroResponse:
        log_failure(
            logger,
            logging.ERROR,
            self.settings.log_sensitive_data,
            "Error consultando Catastro",
            exc,
        )
        invalid = isinstance(exc, ValidationError)
        timeout = isinstance(exc, (TimeoutError, httpx.TimeoutException))
        return CatastroResponse(
            referencia_catastral=referencia,
            estado_consulta="error_formato" if invalid else "error",
            codigo_error=(
                "ENTRADA_INVALIDA" if invalid else "TIMEOUT" if timeout else "ERROR_SERVICIO"
            ),
            mensaje_error=(
                "Entrada inválida"
                if invalid
                else "Tiempo de consulta agotado" if timeout else str(exc)
            ),
        )

    async def consultar_por_referencia(
        self, referencia: str, incluir_raw: bool = False
    ) -> CatastroResponse:
        try:
            ref = ReferenciaCatastral(referencia=referencia).referencia
            return await self._consultar_referencia(ref, "inmueble", incluir_raw)
        except Exception as exc:
            return self._error(referencia, exc)

    async def consultar_parcela_por_codigo(
        self, codigo_parcela: str, incluir_raw: bool = False
    ) -> CatastroResponse:
        ref = ReferenciaCatastral.normalizar(codigo_parcela)
        if not ReferenciaCatastral.analizar_referencia_detallado(ref)["es_codigo_parcela"]:
            return CatastroResponse(
                referencia_catastral=ref,
                estado_consulta="error_formato",
                codigo_error="ENTRADA_INVALIDA",
                mensaje_error="Código de parcela inválido",
            )
        try:
            return await self._consultar_referencia(ref, "parcela", incluir_raw)
        except Exception as exc:
            return self._error(ref, exc)

    async def _consultar_referencia(
        self, ref: str, kind: str, incluir_raw: bool
    ) -> CatastroResponse:
        raw = await self._request(
            CatastroEndpoints.CONSULTA_DNPRC, {"Provincia": "", "Municipio": "", "RefCat": ref}
        )
        return self._construir_respuesta_catastral(ref, raw, kind, incluir_raw)

    async def _request(self, endpoint: str, params: dict[str, str]) -> dict:
        response = await self._realizar_consulta_con_reintentos(self.base_url + endpoint, params)
        return self._parsear_respuesta_json(response.text)

    def _parsear_respuesta_json(self, content: str) -> dict:
        try:
            data = json.loads(content.lstrip("\ufeff"))
        except json.JSONDecodeError:
            return self._parsear_respuesta_xml(content)
        if not isinstance(data, dict):
            raise ValueError("Respuesta JSON inesperada del Catastro")
        return data

    def _parsear_respuesta_xml(self, content: str) -> dict:
        try:
            root = ET.fromstring(content)
            if root.tag.rsplit("}", 1)[-1].lower() not in {"consulta_dnp", "consulta_coordenadas"}:
                raise ValueError("Error parseando respuesta: raíz XML inesperada")
            return self._xml_a_dict(root)
        except (ET.ParseError, DefusedXmlException) as exc:
            raise ValueError("Error parseando respuesta del Catastro") from exc

    def _xml_a_dict(self, element) -> Any:
        if not len(element):
            return element.text.strip() if element.text and element.text.strip() else {}
        result: dict = {}
        for child in element:
            key = child.tag.rsplit("}", 1)[-1]
            value = self._xml_a_dict(child)
            if key in result:
                result[key] = as_list(result[key]) + [value]
            else:
                result[key] = value
        return result

    @staticmethod
    def _root(raw: dict) -> dict:
        wrapped = [value for key, value in raw.items() if key.lower().endswith("result")]
        root = wrapped[0] if len(wrapped) == 1 else raw
        if not isinstance(root, dict) or not any(
            key in root for key in ("control", "bico", "lrcdnp", "coordenadas", "lerr")
        ):
            raise ValueError("Estructura de respuesta del Catastro no reconocida")
        return root

    def _provider_error(self, root: dict, ref: str) -> CatastroResponse | None:
        errors = root.get("lerr")
        if isinstance(errors, dict):
            errors = errors.get("err", errors)
        errors = [
            {
                "codigo": str(e.get("cod", "DESCONOCIDO")),
                "mensaje": str(e.get("des", "Error del Catastro")),
            }
            for e in as_list(errors)
        ]
        if not errors and int(root.get("control", {}).get("cuerr", 0)) > 0:
            errors = [
                {"codigo": "DESCONOCIDO", "mensaje": "Catastro informó de un error sin detalle"}
            ]
        if not errors:
            return None
        codes = {error["codigo"] for error in errors}
        status = (
            "sin_datos"
            if codes <= {"5", "16"}
            else "error_formato" if codes <= {"4", "76", "77"} else "error"
        )
        return CatastroResponse(
            referencia_catastral=ref,
            estado_consulta=status,
            codigo_error=errors[0]["codigo"],
            errores_origen=errors,
            mensaje_error="; ".join(error["mensaje"] for error in errors),
        )

    def _construir_respuesta_catastral(
        self, referencia: str, datos_raw: dict, kind: str = "inmueble", incluir_raw: bool = False
    ) -> CatastroResponse:
        try:
            root = self._root(datos_raw)
            failure = self._provider_error(root, referencia)
            if failure:
                failure.datos_raw = datos_raw if incluir_raw else None
                return failure
            if root.get("bico"):
                bico = root["bico"]
                items = [self._inmueble(bico["bi"], bico)]
            elif root.get("lrcdnp"):
                items = [self._inmueble(item) for item in as_list(root["lrcdnp"].get("rcdnp"))]
            elif int(root.get("control", {}).get("cudnp", 0)) > 0:
                raise ValueError("Respuesta con inmuebles pero sin datos reconocibles")
            else:
                items = []
            individual = items[0] if len(items) == 1 else None
            result = CatastroResponse(
                referencia_catastral=referencia,
                estado_consulta="exitosa" if items else "sin_datos",
                tipo_resultado=kind,
                inmuebles=items,
                total_inmuebles=len(items),
                requiere_seleccion=len(items) > 1,
                datos_basicos=individual.datos_basicos if individual else None,
                direccion=individual.direccion if individual else None,
                datos_raw=datos_raw if incluir_raw else None,
            )
            expected = int(root.get("control", {}).get("cudnp", len(items)))
            if expected != len(items):
                result.advertencias.append(
                    f"Catastro anuncia {expected} inmuebles; se recibieron {len(items)}"
                )
            return result
        except Exception as exc:
            result = self._error(referencia, exc)
            result.codigo_error = "RESPUESTA_INVALIDA"
            result.datos_raw = datos_raw if incluir_raw else None
            return result

    @staticmethod
    def _inmueble(bi: dict, bico: dict | None = None) -> InmuebleCatastral:
        bico = bico or {}
        rc = bi.get("rc") or bi.get("idbi", {}).get("rc", {})
        reference = "".join(str(rc.get(key, "")) for key in ("pc1", "pc2", "car", "cc1", "cc2"))
        if not ReferenciaCatastral.validar_formato_estatico(reference):
            raise ValueError("Inmueble sin referencia completa en la respuesta")
        dt = bi.get("dt", {})
        locs = dt.get("locs", {})
        location = locs.get("lous") or locs.get("lors") or {}
        urban = location.get("lourb", {})
        rural = location.get("lorus", {})
        road, interior = urban.get("dir", {}), urban.get("loint", {})
        ine = dt.get("loine", {})

        def optional(value):
            return str(value).strip() if value is not None and value != "" else None

        street = " ".join(str(road.get(k, "")) for k in ("tv", "nv")).strip() or None
        address = DireccionCatastral(
            via=street,
            numero=optional(road.get("pnp")),
            bloque=optional(road.get("bq")),
            escalera=optional(interior.get("es")),
            planta=optional(interior.get("pt")),
            puerta=optional(interior.get("pu")),
            codigo_postal=optional(urban.get("dp")),
            texto_completo=optional(bi.get("ldt")),
            municipio=optional(dt.get("nm")),
            provincia=optional(dt.get("np")),
            provincia_codigo_ine=optional(ine.get("cp")),
            municipio_codigo_ine=optional(ine.get("cm")),
            municipio_codigo_catastro=optional(dt.get("cmc")),
            poligono=optional(rural.get("cpp", {}).get("cpo")),
            parcela_rustica=optional(rural.get("cpp", {}).get("cpa")),
            paraje=optional(rural.get("npa")),
        )
        debi = bi.get("debi", {})
        data = DatosBasicosInmueble(
            uso=debi.get("luso"),
            superficie_construida=number(debi.get("sfc")),
            antiguedad=int(debi["ant"]) if debi.get("ant") else None,
            superficie_suelo=number(bico.get("finca", {}).get("dff", {}).get("ss")),
        )
        constructions = bico.get("lcons")
        if isinstance(constructions, dict):
            constructions = constructions.get("cons", constructions)
        parts = []
        for part in as_list(constructions):
            interior = part.get("dt", {}).get("lourb", {}).get("loint", {})
            parts.append(
                ConstruccionCatastral(
                    uso=part.get("lcd"),
                    superficie=number(part.get("dfcons", {}).get("stl")),
                    escalera=optional(interior.get("es")),
                    planta=optional(interior.get("pt")),
                    puerta=optional(interior.get("pu")),
                )
            )
        return InmuebleCatastral(
            referencia_catastral=reference,
            datos_basicos=data,
            direccion=address,
            coeficiente_participacion=number(debi.get("cpt")),
            construcciones=parts,
        )

    async def _realizar_consulta_con_reintentos(
        self,
        url: str,
        params: Dict[str, str],
        headers: Dict[str, str] = None,
    ) -> httpx.Response:
        """Realiza una consulta HTTP con reintentos automáticos"""

        for intento in range(self.max_retries + 1):
            inicio = time.perf_counter()
            endpoint = url.rsplit("/", 1)[-1]
            try:
                logger.info(
                    "Consulta Catastro endpoint=%s intento=%d",
                    endpoint,
                    intento + 1,
                )

                # Usar GET para la nueva API WCF JSON - funciona con parámetros en URL
                if headers:
                    response = await self.http_client.get(url, params=params, headers=headers)
                else:
                    response = await self.http_client.get(url, params=params)
                response.raise_for_status()

                # Verificar que la respuesta no esté vacía
                if not response.text.strip():
                    raise ValueError("Respuesta vacía del servidor")

                logger.info(
                    "Consulta Catastro completada endpoint=%s estado=%d duracion_ms=%.1f",
                    endpoint,
                    response.status_code,
                    (time.perf_counter() - inicio) * 1000,
                )
                return response

            except httpx.TimeoutException:
                if intento < self.max_retries:
                    logger.warning(
                        "Timeout de Catastro endpoint=%s intento=%d; reintentando",
                        endpoint,
                        intento + 1,
                    )
                    await asyncio.sleep(self.retry_delay * (intento + 1))
                else:
                    raise ValueError(ERROR_MESSAGES["TIMEOUT"])

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 503:
                    if intento < self.max_retries:
                        logger.warning(
                            "Catastro no disponible endpoint=%s intento=%d; reintentando",
                            endpoint,
                            intento + 1,
                        )
                        await asyncio.sleep(self.retry_delay * (intento + 1))
                    else:
                        raise ValueError(ERROR_MESSAGES["SERVICIO_NO_DISPONIBLE"])
                else:
                    raise ValueError(f"Error HTTP {e.response.status_code}")

            except Exception as e:
                if intento < self.max_retries:
                    log_failure(
                        logger,
                        logging.WARNING,
                        self.settings.log_sensitive_data,
                        f"Fallo de Catastro endpoint={endpoint} intento={intento + 1}; reintentando",
                        e,
                    )
                    await asyncio.sleep(self.retry_delay * (intento + 1))
                else:
                    raise

    async def consultar_por_coordenadas(
        self, latitud: float, longitud: float, incluir_raw: bool = False
    ) -> CatastroResponse:
        """Localiza parcelas; las coordenadas no identifican una planta/puerta."""
        try:
            coords = Coordenadas(latitud=latitud, longitud=longitud)
            if not (27 <= coords.latitud <= 44 and -19 <= coords.longitud <= 5):
                return CatastroResponse(
                    referencia_catastral="DESCONOCIDA",
                    coordenadas=coords,
                    estado_consulta="error",
                    codigo_error="FUERA_COBERTURA",
                    mensaje_error="Punto fuera del ámbito geográfico admitido por este conector de Catastro",
                )
            raw = await self._request(
                CatastroEndpoints.CONSULTA_RCCOOR,
                {"SRS": "EPSG:4326", "CoorX": str(coords.longitud), "CoorY": str(coords.latitud)},
            )
            root = self._root(raw)
            failure = self._provider_error(root, "DESCONOCIDA")
            if failure:
                failure.coordenadas = coords
                failure.datos_raw = raw if incluir_raw else None
                return failure
            references = self._extraer_referencias_de_coordenadas(root)
            if not references:
                raise ValueError("Respuesta de coordenadas sin parcelas reconocibles")
            parcels = [
                await self.consultar_parcela_por_codigo(ref, incluir_raw) for ref in references
            ]
            failed = [p for p in parcels if p.estado_consulta != "exitosa"]
            if failed:
                result = failed[0]
                result.coordenadas = coords
                result.advertencias.append(
                    "No se pudo completar la consulta de todas las parcelas localizadas"
                )
                return result
            if len(parcels) == 1:
                result = parcels[0]
            else:
                items = {i.referencia_catastral: i for p in parcels for i in p.inmuebles}
                result = CatastroResponse(
                    referencia_catastral="BUSQUEDA_COORDENADAS",
                    inmuebles=list(items.values()),
                    total_inmuebles=len(items),
                    requiere_seleccion=len(items) > 1,
                )
            result.tipo_resultado = "localizacion"
            result.coordenadas = coords
            result.advertencias.append(
                "Las coordenadas localizan la parcela; seleccione el inmueble por escalera, planta y puerta"
            )
            if incluir_raw:
                result.datos_raw = {"coordenadas": raw, "parcelas": [p.datos_raw for p in parcels]}
            return result
        except Exception as exc:
            return self._error("DESCONOCIDA", exc)

    @staticmethod
    def _extraer_referencias_de_coordenadas(root: dict) -> list[str]:
        references = []
        for coord in as_list(root.get("coordenadas", {}).get("coord")):
            pc = coord.get("pc", {})
            reference = str(pc.get("pc1", "")) + str(pc.get("pc2", ""))
            if not ReferenciaCatastral.analizar_referencia_detallado(reference)[
                "es_codigo_parcela"
            ]:
                raise ValueError("Código de parcela inválido en respuesta de coordenadas")
            if reference not in references:
                references.append(reference)
        return references

    async def buscar_por_direccion(
        self,
        provincia: str,
        municipio: str,
        tipo_via: str = "CALLE",
        nombre_via: str = "",
        numero: str = "",
        direccion_original: str = "",
    ) -> CatastroResponse:
        """
        Busca referencias catastrales por dirección postal

        NOTA: La API del Catastro tiene limitaciones significativas para búsquedas por dirección.
        Los endpoints JSON documentados no están disponibles actualmente.

        Args:
            provincia: Nombre de la provincia
            municipio: Nombre del municipio
            tipo_via: Tipo de vía (CALLE, AVENIDA, etc.)
            nombre_via: Nombre de la vía
            numero: Número del inmueble (opcional)

        Returns:
            CatastroResponse indicando las alternativas disponibles
        """
        direccion_mostrar = (
            direccion_original
            if direccion_original
            else f"{tipo_via} {nombre_via} {numero}, {municipio}, {provincia}"
        )
        logger.info("Búsqueda informativa por dirección solicitada")
        log_sensitive(
            logger,
            self.settings.log_sensitive_data,
            "Dirección solicitada: %s",
            direccion_mostrar,
        )

        # Verificar si todos los campos necesarios están presentes
        campos_faltantes = []
        if not provincia:
            campos_faltantes.append("PROVINCIA")
        if not municipio:
            campos_faltantes.append("MUNICIPIO")
        if not nombre_via:
            campos_faltantes.append("NOMBRE_VIA")

        if campos_faltantes:
            mensaje_error = f"""
❌ FORMATO DE DIRECCIÓN INCORRECTO

Faltan los siguientes campos obligatorios: {', '.join(campos_faltantes)}

FORMATO CORRECTO REQUERIDO:
'TIPO_VIA NOMBRE_VIA NUMERO, CODIGO_POSTAL, MUNICIPIO, PROVINCIA'

EJEMPLOS VÁLIDOS:
• "CALLE REYES CATOLICOS 6, 18100, ARMILLA, GRANADA"
• "AVENIDA CONSTITUCION 25, 14011, CORDOBA, CORDOBA"
• "PLAZA MAYOR 1, 28012, MADRID, MADRID"

DIRECCIÓN RECIBIDA: {direccion_mostrar}

Por favor, reintente con el formato correcto.
            """.strip()

            return CatastroResponse(
                referencia_catastral="FORMATO_INCORRECTO",
                estado_consulta="error_formato",
                mensaje_error=mensaje_error,
                datos_raw={
                    "direccion_original": direccion_original,
                    "campos_faltantes": campos_faltantes,
                },
            )

        # Información detallada sobre limitaciones y alternativas
        mensaje_alternativas = f"""
⚠️  BÚSQUEDA POR DIRECCIÓN NO DISPONIBLE

La API oficial del Catastro NO permite búsquedas directas por dirección postal.
Los endpoints JSON documentados no están operativos.

📍 DIRECCIÓN SOLICITADA:
{direccion_mostrar}

✅ ALTERNATIVAS FUNCIONALES:

1. 🌐 SEDE ELECTRÓNICA DEL CATASTRO (Más efectivo):
   → https://sede.catastro.gob.es
   → Ir a "Consulta tu catastro"
   → Buscar por dirección: {direccion_mostrar}
   → Copiar la referencia catastral (20 caracteres)
   → Usar aquí: consultar_catastro_por_referencia

2. 📍 BÚSQUEDA POR COORDENADAS GPS:
   → Abrir Google Maps: {direccion_mostrar}
   → Copiar coordenadas (clic derecho en el punto exacto)
   → Usar: consultar_catastro_por_coordenadas
   → Ejemplo coordenadas: 40.4168, -3.7038

3. 🔍 SI YA TIENES LA REFERENCIA CATASTRAL:
   → Usar: consultar_catastro_por_referencia
   → Formato: 20 caracteres alfanuméricos
   → Ejemplo: 4418928VG4141G0001IW

💡 RECOMENDACIÓN:
La opción MÁS RÁPIDA es buscar en sede.catastro.gob.es y luego usar 
la referencia catastral obtenida con nuestras herramientas MCP.
        """.strip()

        return CatastroResponse(
            referencia_catastral="BUSQUEDA_NO_DISPONIBLE",
            estado_consulta="informacion",
            mensaje_error=mensaje_alternativas,
            direccion=DireccionCatastral(
                via=f"{tipo_via} {nombre_via}",
                numero=numero,
                municipio=municipio,
                provincia=provincia,
            ),
            datos_raw={
                "tipo_respuesta": "informacion_alternativas",
                "direccion_solicitada": f"{tipo_via} {nombre_via} {numero}, {municipio}, {provincia}",
                "alternativas": [
                    "sede.catastro.gob.es",
                    "busqueda_por_coordenadas",
                    "consulta_por_referencia_catastral",
                ],
            },
        )
