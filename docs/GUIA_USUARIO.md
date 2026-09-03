# 📖 Guía de Usuario - Servidor MCP Catastro 100% Puro

## 🎯 Introducción

**Servidor MCP (Model Context Protocol) 100% real** para consultar datos del **Catastro de España** directamente desde **Claude Code**. Sin dependencias web, sin Docker, solo lo esencial.

---

## 🚀 Instalación y Configuración

### 📋 Prerrequisitos
- Python 3.14
- uv 0.9.7+
- Claude Code instalado

### 🔧 Instalación

1. **Instalar dependencias:**
```powershell
cd C:\Users\Pablo\Desktop\obratec_app\mcp_catastro
uv sync --locked
```

2. **Configurar entorno (opcional):**
```powershell
cp .env.example .env
# Editar .env para configurar OpenAI API key si deseas IA real
```

3. **Ejecutar servidor MCP:**
```powershell
uv run --locked python mcp_server.py
```

4. **Configurar Claude Code:**
```powershell
# Opción A: Usar archivo de configuración (recomendado)
claude --mcp-config claude-config.json

# Opción B: Configuración directa
claude --mcp-config claude-config.json
```

---

## 🛠️ Herramientas MCP Disponibles

### 1. **Consultar por Referencia Catastral**
```
Herramienta: consultar_catastro_por_referencia
Entrada: referencia catastral de 20 caracteres
```

**Ejemplo con Claude Code:**
```
Usuario: "Consulta la referencia catastral 2749704YJ0624N0001DI"

Claude usará automáticamente la herramienta y mostrará:
- Datos básicos del inmueble
- Dirección catastral
- Superficie construida
- Año de construcción
- Uso del inmueble
```

### 2. **Consultar por Coordenadas**
```
Herramienta: consultar_catastro_por_coordenadas  
Entrada: latitud y longitud (España: 35-44°N, -10-5°E)
```

**Ejemplo con Claude Code:**
```
Usuario: "¿Qué inmueble hay en las coordenadas 40.4168, -3.7038?"

Claude encontrará automáticamente:
- Referencia catastral del inmueble
- Datos completos de la parcela
- Información de construcción
```

### 3. **Generar Resumen IA**
```
Herramienta: generar_resumen_ia
Entrada: referencia + opciones (idioma, usar_openai)
```

**Ejemplo con Claude Code:**
```
Usuario: "Haz un resumen profesional de la referencia 2749704YJ0624N0001DI"

Claude generará:
📋 Resumen Catastral
**Referencia:** 2749704YJ0624N0001DI
**Uso:** Residencial
**Superficie construida:** 92 m²
**Año construcción:** 2007
🏠 Inmueble contemporáneo (10-30 años)
```

### 4. **Validar Referencia**
```
Herramienta: validar_referencia_catastral
Entrada: referencia a validar
```

**Ejemplo con Claude Code:**
```
Usuario: "¿Es válida la referencia 1234567AB1234C1234DE?"

Claude responderá:
"Referencia catastral válida: 1234567AB1234C1234DE"
```

---

## 💡 Ejemplos de Uso con Claude Code

### **Consultas Naturales:**
- "¿Qué datos tiene esta referencia catastral?"
- "Consulta qué hay en Madrid centro"  
- "Resume los datos de esta parcela"
- "Busca por coordenadas y luego haz un resumen"

### **Preguntas Específicas:**
- "¿Cuál es el uso de la referencia 2749704YJ0624N0001DI?"
- "¿Qué superficie tiene el inmueble en las coordenadas 40.4168, -3.7038?"
- "Valida esta referencia: 9872023VH5797H0001JU"

### **Análisis Complejos:**
- "Compara estas dos referencias catastrales"
- "Busca inmuebles cerca de esta coordenada"
- "Explícame el formato de las referencias catastrales"

---

## 🧠 Sistema de IA Integrado

### 🎭 **Modo Simulado** (por defecto)
- ✅ **Sin coste** - No requiere API keys
- 🚀 **Respuesta instantánea** - Procesamiento local
- 📊 **Análisis automático** - Interpreta datos catastrales
- 🌍 **Multiidioma** - Español, inglés, catalán

### 🧮 **Modo OpenAI** (opcional)
- 🔑 **Requiere API key** - Configura en `.env`
- 🧠 **Análisis avanzado** - Mayor precisión y contexto
- 💰 **Coste por uso** - Según tarifas OpenAI
- 🎯 **Resúmenes profesionales** - Calidad superior

### 📝 **Configurar OpenAI:**
```powershell
# En archivo .env
CATASTRO_OPENAI_API_KEY=sk-tu-clave-aqui
CATASTRO_OPENAI_MODEL=gpt-4
CATASTRO_OPENAI_TEMPERATURE=0.3
```

---

## 📝 Referencias Catastrales - Formato Oficial

### ✅ **Formato Válido (20 caracteres):**
```
2749704YJ0624N0001DI
│││││││││││││││││││└── 2 letras: dígitos control
│││││││││││││││└────── 4 dígitos: subparcela  
││││││││││││└────────── 1 letra: coordenada Z
│││││││││└─────────────── 4 dígitos: coordenada Y
│││││└──────────────────── 2 letras: coordenada X
└────────────────────────── 7 dígitos: identificador parcela
```

### ❌ **Formatos Inválidos:**
- `2749704YJ0624N0001` (muy corta, falta DI)
- `2749704YJ0624N0001DI5` (muy larga)  
- `2749704yj0624n0001di` (minúsculas no permitidas)
- `A749704YJ0624N0001DI` (letra en posición numérica)

### 📋 **Referencias de Prueba:**
```
2749704YJ0624N0001DI  # Madrid ejemplo
4707801YJ0675N0001JE  # Barcelona ejemplo  
8077801YJ0687N0001LE  # Valencia ejemplo
```

---

## 🌍 Coordenadas Válidas para España

### ✅ **Rangos Válidos:**
- **Latitud:** 35.0° - 44.0° Norte
- **Longitud:** -10.0° - 5.0° Este

### 📍 **Coordenadas de Prueba:**
```
Madrid Centro:    40.4168, -3.7038
Barcelona:        41.3851, 2.1734
Valencia:         39.4699, -0.3763
Sevilla:          37.3891, -5.9845
Bilbao:           43.2627, -2.9253
```

---

## 🚨 Resolución de Problemas

### **Errores Comunes:**

| Error | Causa | Solución |
|-------|-------|----------|
| `uv.lock` ausente o desactualizado | El entorno no coincide | Ejecutar `uv lock` y revisar el cambio |
| `Referencia catastral inválida` | Formato incorrecto | Verificar 20 caracteres y patrón |
| `Coordenadas fuera de rango` | No están en España | Usar rangos válidos |
| `Servicio no disponible` | Catastro caído | Reintentar más tarde |
| `Timeout` | Respuesta lenta | Aumentar `CATASTRO_CATASTRO_TIMEOUT` en `.env` |

### **Diagnóstico:**

```powershell
# Probar conectividad
uv run --locked python tests/test-startup.py

# Verificar configuración
uv run --locked python -c "from config.settings import get_settings; print(get_settings().catastro_base_url)"

# Debug mode
# En .env: CATASTRO_DEBUG=true
```

---

## 🧪 Testing y Verificación

### **Pruebas Rápidas:**
```powershell
# Test completo de conectividad
uv run --locked python tests/test-startup.py

# Tests unitarios
uv run --locked pytest -q

# Test específico de validación
uv run --locked pytest -q
```

### **Verificar que todo funciona:**
1. `uv run --locked python mcp_server.py` (debe iniciar sin errores)
2. En otra terminal: `claude --mcp-config claude-config.json`
3. Preguntar a Claude: "Valida la referencia 2749704YJ0624N0001DI"

---

## ⚙️ Configuración Avanzada

### **Variables de Entorno Principales:**
```bash
# Configuración básica
CATASTRO_DEBUG=true                    # Activar logs detallados
CATASTRO_LOG_LEVEL=DEBUG               # Nivel de logging
CATASTRO_LOG_SENSITIVE_DATA=false      # No exponer datos catastrales
CATASTRO_CATASTRO_TIMEOUT=60           # Timeout en segundos

# OpenAI (opcional)
CATASTRO_OPENAI_API_KEY=sk-xxx         # Tu API key
CATASTRO_OPENAI_MODEL=gpt-3.5-turbo    # Modelo a usar
```

### **Personalización de Logs:**
```bash
# Logs operativos detallados, siempre por stderr
CATASTRO_LOG_LEVEL=DEBUG

# Solo en un diagnóstico controlado, habilitar además datos sensibles
CATASTRO_LOG_SENSITIVE_DATA=true
```

---

## ❓ Preguntas Frecuentes

**P: ¿Necesito Docker para ejecutar MCP?**
R: No, MCP se ejecuta localmente con Python. Docker era innecesario.

**P: ¿Funciona sin conexión a internet?**
R: No, necesita acceso a `ovc.catastro.meh.es`

**P: ¿Puedo consultar catastros de otros países?**  
R: No, solo España y territorios españoles

**P: ¿Los resúmenes IA cuestan dinero?**
R: El modo simulado es gratis. OpenAI requiere API key de pago.

**P: ¿Hay límites de consultas?**
R: El proyecto no aplica actualmente un rate limit propio. Evita cargas intensivas y respeta las condiciones del servicio oficial.

**P: ¿Cómo sé si está funcionando?**
R: Ejecuta `uv run --locked python tests/test-startup.py` para verificar.

---

## 🆘 Soporte y Ayuda

### **Recursos:**
- **Logs:** `stderr` del proceso MCP
- **Config:** `claude-config.json`
- **Tests:** `uv run --locked pytest -q`
- **Docs:** Carpeta `docs/`

### **Comandos Útiles:**
```powershell
# Verificar instalación
uv run --locked python -c "import mcp; print('MCP OK')"

# Ver configuración actual
uv run --locked python -c "from config.settings import get_settings; s=get_settings(); print(f'URL: {s.catastro_base_url}')"

# Test rápido de referencia
uv run --locked python -c "from models.catastro_models import ReferenciaCatastral; print(ReferenciaCatastral.validar_formato_estatico('2749704YJ0624N0001DI'))"
```

---

## 🎉 ¡Todo Listo!

1. `uv sync --locked`
2. `uv run --locked python mcp_server.py`
3. `claude --mcp-config claude-config.json`
4. **Pregunta a Claude sobre cualquier referencia catastral**

¡Disfruta de tu servidor MCP 100% funcional para el Catastro de España!
