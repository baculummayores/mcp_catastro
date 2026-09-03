# 🏠 MCP Catastro España - Servidor MCP Oficial

[![Python 3.14](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/downloads/)
[![MCP SDK v2](https://img.shields.io/badge/MCP%20SDK-v2-green.svg)](https://modelcontextprotocol.io/)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-ready-purple.svg)](https://claude.ai/code)
[![Catastro España](https://img.shields.io/badge/Catastro-España-red.svg)](https://sede.catastro.gob.es/)

**Servidor MCP (Model Context Protocol) profesional** para consultas al **Catastro de España** con capacidades de IA. Diseñado específicamente para **Claude Code** usando endpoints oficiales del gobierno español.

## ✨ Características Principales

- 🔌 **MCP Python SDK v2** - `MCPServer`, salida estructurada y validación automática
- 🏛️ **API oficial del Catastro** - Endpoints WCF del gobierno español  
- 🏢 **División horizontal** - Consulta parcelas con múltiples inmuebles
- 🧠 **Resúmenes IA** con OpenAI o simulación local
- 🔍 **Validación completa** - Referencias de 14 y 20 caracteres
- 📍 **Consultas por coordenadas** - Localización GPS precisa
- ⚡ **Dependencias mínimas** - Solo 6 librerías esenciales

---

## 🏗️ Arquitectura del Proyecto

```
mcp_catastro/
├── 🚀 mcp_server.py              # Servidor MCP principal
├── 📄 claude-config.json         # Configuración Claude Code
├── 🔧 services/
│   ├── catastro_service.py       # API oficial del Catastro
│   ├── ai_summary.py             # Sistema de IA integrado
│   └── __init__.py
├── 📊 models/
│   ├── catastro_models.py        # Modelos Pydantic + validación
│   └── __init__.py
├── ⚙️ config/
│   ├── settings.py               # Configuración centralizada
│   └── __init__.py
├── 🧪 tests/                     # Tests automatizados
├── 📖 docs/                      # Documentación completa
├── 📄 Guia_Completa_API_Catastro.md  # Documentación API oficial
├── 📋 pyproject.toml            # Dependencias directas y herramientas
├── 🔒 uv.lock                   # Resolución universal reproducible
└── 🛠️ setup-env.ps1              # Script configuración automática
```

---

## 🚀 Instalación Rápida

### 📋 Prerrequisitos

- **Python 3.14**
- **uv 0.9.7+**
- **Claude Code** instalado
- **Windows/Linux/macOS**

### ⚡ Setup Automático (Windows)

```powershell
# Clonar el repositorio
git clone https://github.com/CabhuDev/mcp_Catastro.git
cd mcp_Catastro

# Ejecutar setup automático
.\setup-env.ps1

# Configurar Claude Code
claude --mcp-config claude-config.json
```

### 🔧 Setup Manual

```bash
# Instalar exactamente las versiones bloqueadas
uv sync --locked

# Ejecutar servidor MCP
uv run --locked python mcp_server.py

# En otra terminal, configurar Claude Code
claude --mcp-config claude-config.json
```

El proyecto requiere Python 3.14 (`>=3.14,<3.15`) y usa el transporte
`stdio` por defecto. La API v1 del SDK (`Server` con decoradores de bajo nivel e
`InitializationOptions` manual) ya no se utiliza.

Para habilitar la integración opcional con OpenAI usa
`uv sync --locked --extra openai`. No edites `uv.lock` manualmente; actualiza
`pyproject.toml` y ejecuta `uv lock` cuando quieras cambiar dependencias.

### Verificación

```bash
uv run --locked pytest -q
```

Las pruebas MCP usan el cliente oficial en memoria, negocian la versión de
protocolo vigente y comprueban herramientas, esquemas, salida estructurada y
recursos sin realizar llamadas externas al Catastro.

---

## 🛠️ Herramientas MCP Disponibles

### 1. 🏠 `consultar_catastro_por_referencia`
Consulta **inmueble específico** por referencia catastral de 20 caracteres.

```json
{
  "referencia": "2314501EG1421S0001KJ"
}
```

**Devuelve:** Uso, superficie, año construcción, dirección completa, provincia, municipio.

---

### 2. 🏢 `consultar_parcela_por_codigo` 
**¡NUEVA!** Consulta **parcelas con división horizontal** usando código de 14 caracteres.

```json
{
  "codigo_parcela": "2314501EG1421S"
}
```

**Devuelve:** Lista completa de todos los inmuebles en la parcela, coeficientes de participación, escaleras, plantas, puertas.

---

### 3. 📍 `consultar_catastro_por_coordenadas`
Localiza inmuebles por **coordenadas GPS**.

```json
{
  "latitud": 41.915,
  "longitud": 3.165
}
```

**Devuelve:** Referencia catastral del inmueble en esas coordenadas + datos completos.

---

### 4. ✅ `validar_referencia_catastral`
Valida y analiza referencias catastrales (14 o 20 caracteres).

```json
{
  "referencia": "2314501EG1421S"
}
```

**Devuelve:** Análisis detallado, componentes (provincia, municipio, sector), estado de validez, guía para completar.

---

### 5. 🧠 `generar_resumen_ia`
Genera resumen profesional usando IA.

```json
{
  "referencia": "2314501EG1421S0001KJ",
  "usar_openai": false,
  "idioma": "es"
}
```

**Devuelve:** Resumen estructurado, puntos clave, valoración profesional.

---

### 6. ℹ️ `buscar_catastro_por_direccion`
Herramienta informativa sobre limitaciones de búsqueda por dirección.

```json
{
  "direccion_completa": "CALLE REYES CATOLICOS 6, 18100, ARMILLA, GRANADA"
}
```

**Devuelve:** Explicación de limitaciones + alternativas funcionales.

---

## 🎯 Casos de Uso Reales

### 🏢 Consulta de Edificio Comercial

**Entrada:** `2314501EG1421S` (código de parcela)

**Resultado:**
```
PARCELA CON DIVISION HORIZONTAL ENCONTRADA

Codigo de parcela: 2314501EG1421S
Inmuebles encontrados: 7

INMUEBLES EN LA PARCELA:

1. INMUEBLE 0001: 6.863 m² - Comercial - Escalera 1, Planta 00, Puerta 1
2. INMUEBLE 0002: 3.449 m² - Comercial - Escalera 1, Planta 01, Puerta 1  
3. INMUEBLE 0003: 987 m² - Comercial - Escalera 2, Planta 00, Puerta 1
4. INMUEBLE 0004: 422 m² - Comercial - Escalera 2, Planta 00, Puerta 2
5. INMUEBLE 0005: 6.361 m² - Comercial - Escalera 2, Planta 00, Puerta 3
6. INMUEBLE 0006: 1.967 m² - Comercial - Escalera 2, Planta 01, Puerta 4
7. INMUEBLE 0007: 4.514 m² - Comercial - Escalera 2, Planta 01, Puerta 5

Ubicación: LG SUD-1.11 LA FANGA, PALAFRUGELL (GIRONA)
Año construcción: 2013
```

---

## 🔌 API Oficial del Catastro

### ✅ **Endpoints Implementados**

| Método | Endpoint Oficial | Uso |
|--------|-----------------|-----|
| `CONSULTA_DNPRC` | `/OVCServWeb/OVCWcfCallejero/COVCCallejero.svc/json/Consulta_DNPRC` | Referencias 14/20 chars |
| `CONSULTA_RCCOOR` | `/OVCServWeb/OVCWcfCoord/COVCCoordenadas.svc/json/Consulta_RCCOOR` | Coordenadas GPS |

### 🔄 **Características Técnicas**

- ✅ **JSON nativo** - Respuestas JSON del Catastro
- ✅ **Fallback XML** - Compatibilidad total
- ✅ **Reintentos automáticos** - Manejo robusto de errores
- ✅ **Timeout configurable** - 30 segundos por defecto
- ⚠️ **Sin rate limiting, caché ni métricas internas** - Capacidades previstas en el roadmap

---

## 🧠 Sistema de IA Avanzado

### 🎭 **Modo Simulado** (Gratis)
- ✅ **Sin coste** ni dependencias externas
- 🚀 **Respuesta instantánea**
- 📊 **Análisis automático** de datos catastrales
- 🌍 **Multiidioma** (español, inglés, catalán)

### 🧮 **Modo OpenAI** (Opcional)
- 🔑 Requiere API key de OpenAI
- 🧠 **Análisis profesional** avanzado
- 💰 Coste por consulta
- 🎯 **Mayor precisión** y contexto

### 📝 **Ejemplo de Resumen IA**

```markdown
📋 RESUMEN PROFESIONAL CATASTRAL

Referencia: 2314501EG1421S0001KJ
Tipo: Local comercial contemporáneo
Superficie: 6.863 m²
Antigüedad: 11 años (2013)
Ubicación: Zona comercial de Palafrugell, Costa Brava

🏢 CARACTERÍSTICAS:
- Superficie amplia para actividad comercial
- Planta baja con fácil acceso
- Construcción reciente en buen estado
- Zona turística con alto tránsito

💡 VALORACIÓN:
Inmueble comercial bien ubicado en zona de interés turístico.
Superficie adecuada para comercio especializado.
```

---

## 📋 Referencias Catastrales Españolas

### ✅ **Formato 20 Caracteres (Completo)**
```
2314501EG1421S0001KJ
├─────────┤├─┤├──┤├──┤├┤
│         │ │ │   │   └── 2 letras: Control
│         │ │ │   └────── 4 dígitos: Subparcela
│         │ │ └────────── 4 caracteres: Parcela
│         │ └─────────── 3 caracteres: Manzana
│         └──────────── 2 dígitos: Sector
└─────────────────────── 7 caracteres: Provincia+Municipio
```

### ✅ **Formato 14 Caracteres (Parcela)**
```
2314501EG1421S
├─────────┤├─┤├──┤
│         │ │ └────── 4 caracteres: Parcela
│         │ └─────── 3 caracteres: Manzana  
│         └──────── 2 dígitos: Sector
└───────────────── 7 caracteres: Provincia+Municipio
```

---

## ⚙️ Configuración Avanzada

### 📊 **Variables de Entorno**

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `CATASTRO_DEBUG` | Modo debug detallado | `false` |
| `CATASTRO_LOG_LEVEL` | Nivel de logging | `INFO` |
| `CATASTRO_LOG_SENSITIVE_DATA` | Permitir datos sensibles en logs DEBUG | `false` |
| `CATASTRO_CATASTRO_TIMEOUT` | Timeout API (segundos) | `30` |
| `CATASTRO_CATASTRO_MAX_RETRIES` | Reintentos ante fallos transitorios | `3` |
| `CATASTRO_OPENAI_API_KEY` | Clave OpenAI (opcional) | `None` |
| `CATASTRO_OPENAI_MODEL` | Modelo OpenAI | `gpt-4` |

### 🔧 **Archivo .env**

```bash
# Configuración básica
CATASTRO_DEBUG=false
CATASTRO_LOG_LEVEL=INFO
CATASTRO_LOG_SENSITIVE_DATA=false
CATASTRO_CATASTRO_TIMEOUT=30
CATASTRO_CATASTRO_MAX_RETRIES=3

# OpenAI (opcional)
CATASTRO_OPENAI_API_KEY=tu_api_key_aqui
CATASTRO_OPENAI_MODEL=gpt-4
CATASTRO_OPENAI_TEMPERATURE=0.3
```

---

## 🧪 Testing y Calidad

### ⚡ **Ejecutar Tests**

```bash
# Test de conectividad con API oficial
python -c "import asyncio; from services.catastro_service import CatastroService; asyncio.run(CatastroService().consultar_por_referencia('2314501EG1421S0001KJ'))"

# Tests unitarios completos
uv run --locked pytest --cov=services --cov=models --cov=mcp_server

# Test específico de referencias
uv run --locked pytest -q

# Test manual interactivo
uv run --locked python tests/test-manual.py
```

### 🎯 **Cobertura de Tests**

- ✅ **Validación de referencias** - Formatos 14 y 20 caracteres
- ✅ **Servicios de consulta** - Mocks y endpoints reales  
- ✅ **Manejo de errores** - Timeouts y respuestas HTTP erróneas
- ✅ **Parsing JSON/XML** - Respuestas del Catastro
- ✅ **División horizontal** - Múltiples inmuebles
- ✅ **Coordenadas GPS** - Validación rangos España

---

## 🚨 Manejo de Errores y Troubleshooting

### **Errores Comunes**

| Error | Causa | Solución |
|-------|-------|----------|
| `Referencia catastral inválida` | Formato incorrecto | Verificar 20 chars alfanuméricos |
| `Coordenadas fuera de rango` | No están en España | Usar 35-44°N, -10-5°E |
| `Servicio no disponible` | Catastro en mantenimiento | Reintentar en unos minutos |
| `Timeout` | Respuesta muy lenta | Aumentar `CATASTRO_CATASTRO_TIMEOUT` |

### **Diagnóstico**

```bash
# Test de conectividad
uv run --locked python -c "import httpx; print(httpx.get('https://ovc.catastro.meh.es').status_code)"

# Debug operativo sin datos catastrales
export CATASTRO_LOG_LEVEL=DEBUG
uv run --locked python mcp_server.py

# Opt-in explícito para datos sensibles (solo diagnóstico controlado)
export CATASTRO_LOG_SENSITIVE_DATA=true
```

---

## 📚 Documentación Adicional

- 📖 [Guía de Usuario](docs/GUIA_USUARIO.md) - Uso detallado de cada herramienta
- 🛠️ [Guía de Desarrollo](docs/MCP_DEVELOPMENT_GUIDE.md) - Desarrollo y contribución
- 🗺️ [Roadmap](docs/ROADMAP.md) - Características futuras
- 📄 [API del Catastro](Guia_Completa_API_Catastro.md) - Documentación oficial completa

---

## ❓ FAQ

**¿Funciona sin internet?**  
❌ No, necesita acceso a `ovc.catastro.meh.es`

**¿Consulta otros países?**  
❌ Solo España y territorios españoles

**¿Hay límites de consultas?**  
✅ Sí, 60 por minuto (configurable)

**¿Los resúmenes IA son gratis?**  
✅ Modo simulado gratis, OpenAI requiere API key

**¿Compatible con Claude Code?**  
✅ Diseñado específicamente para Claude Code

**¿Qué es división horizontal?**  
🏢 Parcelas con múltiples inmuebles (pisos, locales, etc.)

---

## 🤝 Contribuir

```bash
# Fork del proyecto
git clone https://github.com/CabhuDev/mcp_Catastro.git

# Crear rama de feature
git checkout -b feature/nueva-funcionalidad

# Hacer cambios y tests
uv run --locked pytest -q

# Commit y push
git commit -m "feat: añadir nueva funcionalidad"
git push origin feature/nueva-funcionalidad

# Crear Pull Request
```

### **Estándares de Código**
- ✅ **Python 3.14** - Runtime único soportado
- ✅ **Pydantic V2** - Validación de datos
- ✅ **Black + isort** - Formato de código
- ✅ **Pytest** - Tests unitarios
- ✅ **Docstrings** - Documentación en código

---

## 📝 Changelog

### 🆕 **v3.0.0 - División Horizontal** (Actual)
- ✅ **Nueva herramienta:** `consultar_parcela_por_codigo`
- ✅ **Soporte completo** para parcelas con múltiples inmuebles
- ✅ **Estructura dual** - Manejo 14 y 20 caracteres
- ✅ **Análisis detallado** - Coeficientes, escaleras, plantas
- ✅ **Documentación actualizada** - Casos de uso reales

### 📚 **v2.0.0 - MCP Puro**
- ✅ Eliminado FastAPI y Docker (innecesarios)
- ✅ MCP 100% real con protocolo stdio
- ✅ Dependencias bloqueadas con `uv.lock`
- ✅ Optimizado para Claude Code

### 🎯 **v1.0.0 - API Oficial**
- ✅ Migración a endpoints WCF oficiales
- ✅ Soporte JSON nativo + fallback XML
- ✅ Sistema de IA integrado

---

## 📄 Licencia

**MIT License** - Libre para uso comercial y personal.

---

## 🆘 Soporte

- **Issues:** [GitHub Issues](https://github.com/CabhuDev/mcp_Catastro/issues)
- **Documentación:** [`docs/`](docs/)
- **Tests:** `uv run --locked pytest -q`
- **Logs:** `stderr` del proceso MCP

---

## 👨‍💻 Autor

**Pablo Cabello Hurtado**  
📧 pablo.cabello.hurtado@gmail.com  
🐙 GitHub: [@CabhuDev](https://github.com/CabhuDev)

---

<div align="center">

**🏠 Hecho con ❤️ para la comunidad española**

[![Catastro España](https://img.shields.io/badge/Datos-Catastro%20España-red.svg)](https://sede.catastro.gob.es/)
[![MCP Protocol](https://img.shields.io/badge/Protocol-MCP-green.svg)](https://modelcontextprotocol.io/)
[![Claude Code](https://img.shields.io/badge/IDE-Claude%20Code-purple.svg)](https://claude.ai/code)

</div>
