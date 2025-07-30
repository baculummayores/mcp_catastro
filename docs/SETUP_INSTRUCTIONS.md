# 🚀 Servidor MCP Catastro - 100% Puro

## 🎯 **MCP REAL PARA CLAUDE CODE**

Servidor MCP completamente limpio y funcional para consultas al **Catastro de España**.

---

## 🔧 **Instalación y Uso:**

### **1. Instalar dependencias:**
```powershell
cd C:\Users\Pablo\Desktop\obratec_app\mcp_catastro
pip install -r requirements.txt
```

### **2. Ejecutar servidor MCP:**
```powershell
python mcp_server.py
```

### **3. Configurar Claude Code:**
```powershell
# Usando archivo de configuración (recomendado)
claude --mcp-config claude-config.json

# O configuración directa
claude --mcp-config '{"mcpServers":{"catastro":{"command":"python","args":["C:\\Users\\Pablo\\Desktop\\obratec_app\\mcp_catastro\\mcp_server.py"],"transport":"stdio"}}}'
```

---

## 🛠️ **Herramientas MCP Disponibles:**

### 1. **Consultar por referencia catastral**
```
consultar_catastro_por_referencia
Entrada: referencia (ej: "2749704YJ0624N0001DI")
```

### 2. **Consultar por coordenadas**
```
consultar_catastro_por_coordenadas  
Entrada: latitud, longitud (ej: 40.4168, -3.7038)
```

### 3. **Generar resumen IA**
```
generar_resumen_ia
Entrada: referencia, usar_openai, idioma
```

### 4. **Validar referencia**
```
validar_referencia_catastral
Entrada: referencia a validar
```

---

## 🧪 **Pruebas:**

```powershell
# Probar conectividad con Catastro
python scripts/test-connection.py

# Tests unitarios
pytest tests/ -v
```

---

## ⚙️ **Configuración (opcional):**

Crea `.env` desde `.env.example` para:
- Configurar OpenAI API key (para IA real)
- Ajustar timeouts y rate limits
- Habilitar debug mode

---

## 📁 **Estructura Simplificada:**

```
mcp_catastro/
├── 🚀 mcp_server.py          # Servidor MCP principal
├── 🔧 services/              # Lógica de consultas
├── 📊 models/                # Modelos de datos
├── ⚙️ config/                # Configuración
├── 🧪 tests/                 # Tests
├── 🛠️ scripts/               # Utilidades
├── 📖 docs/                  # Documentación
├── 📄 claude-config.json     # Config Claude Code
└── 📋 requirements.txt       # Dependencias mínimas
```

---

## ✅ **Características:**

- ✅ **MCP 100% real** - Compatible con Claude Code
- ✅ **API WCF oficial** - Endpoints actualizados del Catastro
- ✅ **Dependencias mínimas** - Solo lo esencial
- ✅ **Sin Docker** - Ejecuta localmente como debe ser
- ✅ **4 herramientas** - Consultas completas al Catastro
- ✅ **IA integrada** - Resúmenes automáticos o con OpenAI

---

## 🎉 **¡Listo para usar con Claude Code!**

1. `pip install -r requirements.txt`
2. `python mcp_server.py`  
3. `claude --mcp-config claude-config.json`
4. Pregunta a Claude sobre cualquier referencia catastral