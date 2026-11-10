from copy import deepcopy

import httpx
import pytest

from mcp_server import parse_direccion_completa
from services.catastro_service import CatastroService
from tests.test_catastro_responses import fixture


def address_response(request):
    path = request.url.path
    if path.endswith("ObtenerMunicipios"):
        return httpx.Response(200, json=fixture("municipalities"))
    if path.endswith("ObtenerCallejero"):
        assert request.url.params["NomVia"] == "REYES CATOLICOS"
        return httpx.Response(200, json=fixture("streets"))
    assert path.endswith("Consulta_DNPLOC")
    assert request.url.params["Sigla"] == "CL"
    assert request.url.params["Calle"] == "REYES CATOLICOS"
    assert request.url.params["Numero"] == "6"
    return httpx.Response(200, json=fixture("address"))


@pytest.mark.asyncio
async def test_real_address_list_and_interior_parameters():
    calls = []

    def handler(request):
        calls.append(request)
        return address_response(request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await CatastroService(client).buscar_por_direccion(
            "GRANADA",
            "ARMILLA",
            "CALLE",
            "REYES CATOLICOS",
            "6",
            escalera="1",
            planta="00",
            puerta="A",
        )
    assert result.estado_consulta == "exitosa"
    assert result.total_inmuebles == 22 and result.requiere_seleccion
    assert calls[-1].url.params["Escalera"] == "1"
    assert calls[-1].url.params["Puerta"] == "A"
    assert result.inmuebles[12].referencia_catastral == "4611123VG4141B0013RS"


@pytest.mark.asyncio
async def test_ambiguous_streets_are_not_arbitrarily_selected():
    def handler(request):
        if request.url.path.endswith("ObtenerMunicipios"):
            return httpx.Response(200, json=fixture("municipalities"))
        assert request.url.path.endswith("ObtenerCallejero")
        raw = deepcopy(fixture("streets"))
        street = deepcopy(raw["consulta_callejeroResult"]["callejero"]["calle"][0])
        street["dir"]["tv"] = "AV"
        street["dir"]["cv"] = "183"
        raw["consulta_callejeroResult"]["callejero"]["calle"].append(street)
        return httpx.Response(200, json=raw)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await CatastroService(client).buscar_por_direccion(
            "GRANADA", "ARMILLA", nombre_via="REYES CATOLICOS", numero="6"
        )
    assert result.estado_consulta == "requiere_seleccion"
    assert len(result.candidatos) == 2
    assert {c.tipo_via for c in result.candidatos} == {"CL", "AV"}
    assert not result.inmuebles


@pytest.mark.asyncio
async def test_missing_number_returns_street_without_unbounded_property_search():
    async with httpx.AsyncClient(transport=httpx.MockTransport(address_response)) as client:
        result = await CatastroService(client).buscar_por_direccion(
            "GRANADA", "ARMILLA", nombre_via="REYES CATOLICOS"
        )
    assert result.estado_consulta == "requiere_seleccion"
    assert "número" in result.advertencias[0]


@pytest.mark.parametrize(
    "text,name,number",
    [
        ("CALLE MAYOR, MADRID, MADRID", "MAYOR", ""),
        ("CALLE MAYOR 3 BIS, MADRID, MADRID", "MAYOR", "3 BIS"),
        ("AVENIDA DEL 2 DE MAYO 6, 28000, MADRID, MADRID", "DEL 2 DE MAYO", "6"),
        ("CL MAYOR S/N, MADRID, MADRID", "MAYOR", "S/N"),
    ],
)
def test_text_adapter_does_not_treat_street_name_as_number(text, name, number):
    result = parse_direccion_completa(text)
    assert result["nombre_via"] == name and result["numero"] == number


def street_response(*streets):
    raw = deepcopy(fixture("streets"))
    root = raw["consulta_callejeroResult"]
    root["control"]["cuca"] = len(streets)
    root["callejero"]["calle"] = [
        {"dir": {"cv": str(index), "tv": kind, "nv": name}}
        for index, (kind, name) in enumerate(streets)
    ]
    return raw


def street_error(code="10"):
    return {
        "consulta_callejeroResult": {
            "control": {"cuerr": 1},
            "lerr": [{"cod": code, "des": "NO HAY COINCIDENCIAS EN LA BÚSQUEDA DE VÍAS"}],
        }
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "name,queries",
    [
        ("de Mozart", ["de Mozart", "Mozart"]),
        ("de los Olmos", ["de los Olmos", "los Olmos", "Olmos"]),
        ("de las Flores", ["de las Flores", "las Flores", "Flores"]),
        ("de la Paz", ["de la Paz", "la Paz", "Paz"]),
        ("del Prado", ["del Prado", "el Prado", "Prado"]),
        (
            "DE LOS Reyes de España",
            ["DE LOS Reyes de España", "LOS Reyes de España", "Reyes de España"],
        ),
    ],
)
@pytest.mark.parametrize("empty_response", [False, True])
async def test_leading_particle_fallback_requires_selection(name, queries, empty_response):
    searched = []

    def handler(request):
        if request.url.path.endswith("ObtenerMunicipios"):
            return httpx.Response(200, json=fixture("municipalities"))
        assert request.url.path.endswith("ObtenerCallejero")
        searched.append(request.url.params["NomVia"])
        if len(searched) < len(queries):
            return httpx.Response(200, json=street_response() if empty_response else street_error())
        return httpx.Response(200, json=street_response(("CL", queries[-1].upper())))

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await CatastroService(client).buscar_por_direccion(
            "GRANADA", "ARMILLA", "CL", name, "46"
        )
    assert searched == queries
    assert result.estado_consulta == "requiere_seleccion"
    assert result.requiere_seleccion
    assert result.candidatos[0].nombre == queries[-1].upper()
    assert not result.inmuebles


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "name", ["DE LOS OLMOS", "DE LAS FLORES", "DE LA PAZ", "DEL PRADO", "LA PAZ"]
)
async def test_original_official_name_is_used_without_removing_particles(name):
    searched = []

    def handler(request):
        if request.url.path.endswith("ObtenerMunicipios"):
            return httpx.Response(200, json=fixture("municipalities"))
        if request.url.path.endswith("ObtenerCallejero"):
            searched.append(request.url.params["NomVia"])
            return httpx.Response(200, json=street_response(("CL", name)))
        assert request.url.params["Calle"] == name
        assert request.url.params["Numero"] == "46"
        return httpx.Response(200, json=fixture("address"))

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await CatastroService(client).buscar_por_direccion(
            "GRANADA", "ARMILLA", "CL", name, "46"
        )
    assert searched == [name]
    assert result.estado_consulta == "exitosa"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "streets", [[("CL", "MOZART")], [("CL", "MOZART"), ("CL", "MOZART NORTE")]]
)
async def test_partial_street_matches_are_offered_without_choosing_a_property(streets):
    def handler(request):
        if request.url.path.endswith("ObtenerMunicipios"):
            return httpx.Response(200, json=fixture("municipalities"))
        assert request.url.path.endswith("ObtenerCallejero")
        return httpx.Response(200, json=street_response(*streets))

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await CatastroService(client).buscar_por_direccion(
            "GRANADA", "ARMILLA", nombre_via="MOZ", numero="46"
        )
    assert result.estado_consulta == "requiere_seleccion"
    assert len(result.candidatos) == len(streets)
    assert not result.inmuebles


@pytest.mark.asyncio
async def test_selecting_fallback_street_preserves_number_and_street_type():
    searched = []

    def handler(request):
        if request.url.path.endswith("ObtenerMunicipios"):
            return httpx.Response(200, json=fixture("municipalities"))
        if request.url.path.endswith("ObtenerCallejero"):
            searched.append(request.url.params["NomVia"])
            if searched[-1] == "de Mozart":
                return httpx.Response(200, json=street_error())
            return httpx.Response(200, json=street_response(("CL", "MOZART"), ("AV", "MOZART")))
        assert request.url.params["Sigla"] == "AV"
        assert request.url.params["Calle"] == "MOZART"
        assert request.url.params["Numero"] == "46"
        return httpx.Response(200, json=fixture("address"))

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        service = CatastroService(client)
        result = await service.buscar_por_direccion(
            "GRANADA", "ARMILLA", nombre_via="de Mozart", numero="46"
        )
        assert result.estado_consulta == "requiere_seleccion"
        assert len(result.candidatos) == 2
        selected = next(c for c in result.candidatos if c.tipo_via == "AV")
        result = await service.buscar_por_direccion(
            "GRANADA", "ARMILLA", selected.tipo_via, selected.nombre, "46"
        )
    assert searched == ["de Mozart", "Mozart", "MOZART"]
    assert result.estado_consulta == "exitosa"


@pytest.mark.asyncio
@pytest.mark.parametrize("code,expected_calls,status", [("10", 3, "sin_datos"), ("99", 1, "error")])
async def test_exhausted_variants_and_service_errors_remain_distinct(code, expected_calls, status):
    searched = []

    def handler(request):
        if request.url.path.endswith("ObtenerMunicipios"):
            return httpx.Response(200, json=fixture("municipalities"))
        assert request.url.path.endswith("ObtenerCallejero")
        searched.append(request.url.params["NomVia"])
        return httpx.Response(200, json=street_error(code))

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await CatastroService(client).buscar_por_direccion(
            "GRANADA", "ARMILLA", nombre_via="de las Flores", numero="46", incluir_raw=True
        )
    assert len(searched) == expected_calls
    assert result.estado_consulta == status
    assert result.codigo_error == code
    assert result.datos_raw == street_error(code)
