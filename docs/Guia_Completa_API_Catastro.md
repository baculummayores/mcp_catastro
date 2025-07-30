# 📘 Guía Completa de los Servicios Web Libres del Catastro de España

Esta guía técnica resume de forma detallada los servicios REST y SOAP disponibles en la Sede Electrónica del Catastro para obtener datos públicos no protegidos. Incluye todos los métodos oficiales, ejemplos de uso, estructura de respuesta y cómo conectarse desde tu app o backend.

---

## ✅ Qué puedes hacer con esta API

- Obtener datos catastrales a partir de:
  - Referencia Catastral
  - Dirección (Provincia, Municipio, Vía, Número)
  - Coordenadas (X, Y)
  - Polígono y parcela
- Obtener calles, municipios y provincias
- Convertir coordenadas ↔ Referencias catastrales
- Acceder a parcelas cercanas a un punto

---

## 🔌 Tipos de Acceso

### 1. REST (Recomendado para uso rápido y JSON)

- Base de endpoint:  
  `https://ovc.catastro.meh.es/OVCServWeb/OVCWcfCallejero/[Servicio].svc/json/[Método]`

- Formato de respuesta:  
  JSON o XML (por defecto XML si no se usa `/json`)

- Ejemplo (por RC):  
  `https://ovc.catastro.meh.es/OVCServWeb/OVCWcfCallejero/COVCCallejero.svc/json/Consulta_DNPRC?RefCat=2749704YJ0624N0001DI`

---

### 2. SOAP (Completo, más verboso)

- WSDL:  
  `https://ovc.catastro.meh.es/OVCServWeb/OVCWcfCallejero/COVCCallejero.svc?singleWsdl`

- Requiere cliente SOAP (Zeep, Postman, SoapUI, etc.)

---

## 🔍 Métodos Disponibles

### 📍 Callejero y Datos por Localización

| Método                | Parámetros                                         | Descripción |
|----------------------|----------------------------------------------------|-------------|
| `ConsultaProvincia`  | Ninguno                                            | Devuelve todas las provincias |
| `ConsultaMunicipio`  | `Provincia`                                        | Devuelve municipios por provincia |
| `ConsultaVia`        | `Provincia`, `Municipio`                           | Devuelve calles de un municipio |
| `ConsultaNumero`     | `Provincia`, `Municipio`, `Vía`                    | Devuelve los números de una vía |
| `Consulta_DNPLOC`    | `Provincia`, `Municipio`, `Vía`, `Número`, `Bloque`, `Escalera`, `Planta`, `Puerta` | Consulta un inmueble por dirección completa |
| `Consulta_DNPRC`     | `RefCat`                                           | Consulta un inmueble por referencia catastral |
| `Consulta_DNPPP`     | `Provincia`, `Municipio`, `Polígono`, `Parcela`    | Consulta un inmueble rústico por polígono y parcela |

---

### 🗺️ Coordenadas y Parcelas

| Método                      | Parámetros                       | Descripción |
|----------------------------|----------------------------------|-------------|
| `Consulta_RCCOOR`          | `Coordenada_X`, `Coordenada_Y`   | Devuelve la RC de una parcela en esas coordenadas |
| `Consulta_RCCOOR_Distancia`| `Coordenada_X`, `Coordenada_Y`, `Distancia` | Parcelas cercanas |
| `Consulta_CPMRC`           | `RefCat`                         | Devuelve las coordenadas centroide de la RC |

---

## 🧪 Ejemplos de Uso REST

### 1. Consulta por Referencia Catastral

```http
GET https://ovc.catastro.meh.es/OVCServWeb/OVCWcfCallejero/COVCCallejero.svc/json/Consulta_DNPRC?RefCat=2749704YJ0624N0001DI
```

#### Respuesta esperada:

```json
{
  "consulta_dnp": {
    "bico": {
      "bi": {
        "debi": {
          "luso": "Residencial",
          "sfc": "92",
          "ant": "2007"
        }
      }
    }
  }
}
```

---

### 2. Consulta por Coordenadas

```http
GET https://ovc.catastro.meh.es/OVCServWeb/OVCWcfCoord/COVCCoordenadas.svc/json/Consulta_RCCOOR?SRS=EPSG:4326&Coordenada_X=-3.7038&Coordenada_Y=40.4168
```

---

## 🛠️ Formatos y Reglas

### 🔡 Codificación

- Las coordenadas deben estar en formato **EPSG:4326** (lat/lon estándar)
- Todos los nombres deben ir sin tildes y en mayúsculas

### 📄 Esquemas de Respuesta (XSD)

Los esquemas XML de cada método están en:  
http://www.catastro.hacienda.gob.es/ws/esquemas.htm

---

## ❌ Códigos de Error Comunes

| Código   | Significado                                |
|----------|--------------------------------------------|
| `2 CAL`  | RC no especificada                         |
| `12 CAL` | Provincia no existe                        |
| `33 CAL` | Calle no existe                            |
| `41 CAL` | Número no especificado                     |
| `76 CAL` | Coordenada X no informada                  |

---

## 📚 Recursos Adicionales

- Portal oficial: https://www.sedecatastro.gob.es
- Acceso a servicios web: https://www.sedecatastro.gob.es/OVCFrames.aspx?TIPO=CONSULTA
- Guía técnica (PDF): disponible en el apartado “Servicios web libres”

---

## 📦 Cómo conectarte desde Python

### Usando `httpx`:

```python
import httpx

refcat = "2749704YJ0624N0001DI"
url = f"https://ovc.catastro.meh.es/OVCServWeb/OVCWcfCallejero/COVCCallejero.svc/json/Consulta_DNPRC?RefCat={refcat}"

r = httpx.get(url)
data = r.json()
print(data["consulta_dnp"]["bico"]["bi"]["debi"])
```

---

## 🏢 Ejemplo avanzado: Parcela con División Horizontal

### 📍 Caso real

Parcela en:
```
LG SUD-1.11 LA FANGA
PALAFRUGELL (GIRONA)
Superficie: 14.481 m²
```

Esta parcela presenta varios inmuebles (pisos o locales) inscritos como división horizontal.

---

### 🔍 ¿Cómo consultarla?

#### ✅ Paso 1: Obtener coordenadas

Puedes usar un visor catastral o mapas online para localizar un punto dentro de la parcela.

#### ✅ Paso 2: Consulta RCCOOR (por coordenadas)

```http
GET https://ovc.catastro.meh.es/OVCServWeb/OVCWcfCoord/COVCCoordenadas.svc/json/Consulta_RCCOOR?SRS=EPSG:4326&Coordenada_X=3.165&Coordenada_Y=41.915
```

Esta llamada devolverá una **referencia catastral completa** de 20 dígitos (ejemplo: `1234567AB1234C0001TF`).

---

#### ✅ Paso 3: Obtener RC base y usar `Consulta_DNPRC`

Recorta los primeros **14 dígitos** de la referencia (ejemplo: `1234567AB1234C`) y llama a:

```http
GET https://ovc.catastro.meh.es/OVCServWeb/OVCWcfCallejero/COVCCallejero.svc/json/Consulta_DNPRC?RefCat=1234567AB1234C
```

Esto te devolverá:
- Un listado de **todos los inmuebles** que forman parte de esa división horizontal
- Cada uno con:
  - Referencia catastral individual
  - Superficie construida
  - Uso del inmueble
  - Antigüedad estimada
  - Información adicional (planta, puerta, etc.)

---

### 🧠 ¿Por qué funciona?

Cuando introduces una referencia catastral **de 14 caracteres**, el sistema interpreta que quieres **la unidad base o raíz** de la finca, y devuelve todos los elementos asociados.

---

### 🧪 Alternativa: Consulta por dirección

Si conoces la dirección estructurada exacta, puedes usar:

```
GET /Consulta_DNPLOC
```

Con los parámetros:
- Provincia = GIRONA
- Municipio = PALAFRUGELL
- TipoVía = LG
- NombreVía = SUD-1.11 LA FANGA

Esta consulta es más compleja pero útil si conoces el número o planta.