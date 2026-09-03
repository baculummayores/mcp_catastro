"""
Servicio de IA para generar resúmenes de datos catastrales
"""

import logging
from datetime import datetime

from config.settings import get_settings, log_failure, log_sensitive
from models.catastro_models import CatastroResponse
from services.catastro_service import CatastroService

logger = logging.getLogger(__name__)


class AIService:
    """Servicio para generar resúmenes con IA de datos catastrales"""

    def __init__(self, catastro_service: CatastroService | None = None):
        self.settings = get_settings()
        self.catastro_service = catastro_service or CatastroService()
        self._openai_client = None

    async def generar_resumen(
        self, referencia: str, usar_openai: bool = False, idioma: str = "es"
    ) -> str:
        """
        Genera un resumen profesional de los datos catastrales

        Args:
            referencia: Referencia catastral
            usar_openai: Si usar OpenAI o generar un resumen simulado
            idioma: Idioma del resumen (es, en, ca)

        Returns:
            Resumen textual de los datos
        """
        try:
            # Obtener datos catastrales
            datos_catastro = await self.catastro_service.consultar_por_referencia(referencia)

            if datos_catastro.estado_consulta != "exitosa":
                return f"Error al obtener datos catastrales: {datos_catastro.mensaje_error}"

            # Generar resumen según el método elegido
            if usar_openai and self.settings.openai_api_key:
                return await self._generar_resumen_openai(datos_catastro, idioma)
            else:
                return self._generar_resumen_simulado(datos_catastro, idioma)

        except Exception as e:
            log_failure(
                logger,
                logging.ERROR,
                self.settings.log_sensitive_data,
                "Error generando resumen",
                e,
            )
            log_sensitive(
                logger, self.settings.log_sensitive_data, "Referencia del resumen: %s", referencia
            )
            return f"Error generando resumen: {str(e)}"

    async def _generar_resumen_openai(self, datos: CatastroResponse, idioma: str) -> str:
        """Genera un resumen usando OpenAI"""
        try:
            # Importar OpenAI solo si se va a usar
            import openai

            # Configurar cliente
            if not self._openai_client:
                self._openai_client = openai.AsyncOpenAI(api_key=self.settings.openai_api_key)

            # Preparar prompt según idioma
            prompt = self._construir_prompt(datos, idioma)

            # Llamar a OpenAI
            response = await self._openai_client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt(idioma)},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=self.settings.openai_max_tokens,
                temperature=self.settings.openai_temperature,
            )

            resumen = response.choices[0].message.content.strip()
            logger.info("Resumen generado con OpenAI")
            log_sensitive(
                logger,
                self.settings.log_sensitive_data,
                "Referencia resumida: %s",
                datos.referencia_catastral,
            )

            return resumen

        except Exception as e:
            log_failure(
                logger,
                logging.ERROR,
                self.settings.log_sensitive_data,
                "Error generando resumen con OpenAI",
                e,
            )
            # Fallback a resumen simulado
            return self._generar_resumen_simulado(datos, idioma)

    def _generar_resumen_simulado(self, datos: CatastroResponse, idioma: str) -> str:
        """Genera un resumen simulado sin usar APIs externas"""
        try:
            # Plantillas por idioma
            plantillas = {
                "es": {
                    "inicio": "📋 **Resumen Catastral**\n\n",
                    "referencia": f"**Referencia:** {datos.referencia_catastral}\n",
                    "uso": (
                        "**Uso:** {uso}\n"
                        if datos.datos_basicos and datos.datos_basicos.uso
                        else ""
                    ),
                    "superficie": (
                        "**Superficie construida:** {superficie} m²\n"
                        if datos.datos_basicos and datos.datos_basicos.superficie_construida
                        else ""
                    ),
                    "antiguedad": (
                        "**Año construcción:** {antiguedad}\n"
                        if datos.datos_basicos and datos.datos_basicos.antiguedad
                        else ""
                    ),
                    "direccion": (
                        "**Dirección:** {direccion}\n"
                        if datos.direccion and datos.direccion.via
                        else ""
                    ),
                    "conclusion": "\n✅ Datos obtenidos del Catastro de España",
                },
                "en": {
                    "inicio": "📋 **Cadastral Summary**\n\n",
                    "referencia": f"**Reference:** {datos.referencia_catastral}\n",
                    "uso": (
                        "**Use:** {uso}\n"
                        if datos.datos_basicos and datos.datos_basicos.uso
                        else ""
                    ),
                    "superficie": (
                        "**Built area:** {superficie} m²\n"
                        if datos.datos_basicos and datos.datos_basicos.superficie_construida
                        else ""
                    ),
                    "antiguedad": (
                        "**Construction year:** {antiguedad}\n"
                        if datos.datos_basicos and datos.datos_basicos.antiguedad
                        else ""
                    ),
                    "direccion": (
                        "**Address:** {direccion}\n"
                        if datos.direccion and datos.direccion.via
                        else ""
                    ),
                    "conclusion": "\n✅ Data obtained from Spanish Cadastre",
                },
                "ca": {
                    "inicio": "📋 **Resum Cadastral**\n\n",
                    "referencia": f"**Referència:** {datos.referencia_catastral}\n",
                    "uso": (
                        "**Ús:** {uso}\n" if datos.datos_basicos and datos.datos_basicos.uso else ""
                    ),
                    "superficie": (
                        "**Superfície construïda:** {superficie} m²\n"
                        if datos.datos_basicos and datos.datos_basicos.superficie_construida
                        else ""
                    ),
                    "antiguedad": (
                        "**Any construcció:** {antiguedad}\n"
                        if datos.datos_basicos and datos.datos_basicos.antiguedad
                        else ""
                    ),
                    "direccion": (
                        "**Adreça:** {direccion}\n"
                        if datos.direccion and datos.direccion.via
                        else ""
                    ),
                    "conclusion": "\n✅ Dades obtingudes del Cadastre d'Espanya",
                },
            }

            plantilla = plantillas.get(idioma, plantillas["es"])

            # Construir resumen
            resumen = plantilla["inicio"]
            resumen += plantilla["referencia"]

            if datos.datos_basicos:
                if datos.datos_basicos.uso:
                    resumen += plantilla["uso"].format(uso=datos.datos_basicos.uso)
                if datos.datos_basicos.superficie_construida:
                    resumen += plantilla["superficie"].format(
                        superficie=datos.datos_basicos.superficie_construida
                    )
                if datos.datos_basicos.antiguedad:
                    resumen += plantilla["antiguedad"].format(
                        antiguedad=datos.datos_basicos.antiguedad
                    )

            if datos.direccion and datos.direccion.via:
                direccion_completa = datos.direccion.via
                if datos.direccion.numero:
                    direccion_completa += f", {datos.direccion.numero}"
                resumen += plantilla["direccion"].format(direccion=direccion_completa)

            resumen += plantilla["conclusion"]

            # Añadir análisis automático
            resumen += self._generar_analisis_automatico(datos, idioma)

            logger.info("Resumen simulado generado")
            log_sensitive(
                logger,
                self.settings.log_sensitive_data,
                "Referencia resumida: %s",
                datos.referencia_catastral,
            )
            return resumen

        except Exception as e:
            log_failure(
                logger,
                logging.ERROR,
                self.settings.log_sensitive_data,
                "Error generando resumen simulado",
                e,
            )
            return f"Error generando resumen: {str(e)}"

    def _generar_analisis_automatico(self, datos: CatastroResponse, idioma: str) -> str:
        """Genera un análisis automático básico de los datos"""
        analisis = ""

        try:
            if datos.datos_basicos:
                # Análisis de antigüedad
                if datos.datos_basicos.antiguedad:
                    edad = datetime.now().year - datos.datos_basicos.antiguedad

                    if idioma == "es":
                        if edad < 10:
                            analisis += "\n\n🏗️ **Inmueble moderno** (menos de 10 años)"
                        elif edad < 30:
                            analisis += "\n\n🏠 **Inmueble contemporáneo** (10-30 años)"
                        elif edad < 50:
                            analisis += "\n\n🏛️ **Inmueble establecido** (30-50 años)"
                        else:
                            analisis += "\n\n🏚️ **Inmueble histórico** (más de 50 años)"
                    elif idioma == "en":
                        if edad < 10:
                            analisis += "\n\n🏗️ **Modern building** (less than 10 years)"
                        elif edad < 30:
                            analisis += "\n\n🏠 **Contemporary building** (10-30 years)"
                        elif edad < 50:
                            analisis += "\n\n🏛️ **Established building** (30-50 years)"
                        else:
                            analisis += "\n\n🏚️ **Historic building** (more than 50 years)"
                    else:  # catalán
                        if edad < 10:
                            analisis += "\n\n🏗️ **Immoble modern** (menys de 10 anys)"
                        elif edad < 30:
                            analisis += "\n\n🏠 **Immoble contemporani** (10-30 anys)"
                        elif edad < 50:
                            analisis += "\n\n🏛️ **Immoble establert** (30-50 anys)"
                        else:
                            analisis += "\n\n🏚️ **Immoble històric** (més de 50 anys)"

                # Análisis de superficie
                if datos.datos_basicos.superficie_construida:
                    superficie = datos.datos_basicos.superficie_construida

                    if idioma == "es":
                        if superficie < 50:
                            analisis += "\n📏 **Superficie pequeña** (menos de 50 m²)"
                        elif superficie < 100:
                            analisis += "\n📏 **Superficie media** (50-100 m²)"
                        elif superficie < 200:
                            analisis += "\n📏 **Superficie amplia** (100-200 m²)"
                        else:
                            analisis += "\n📏 **Superficie muy amplia** (más de 200 m²)"
                    elif idioma == "en":
                        if superficie < 50:
                            analisis += "\n📏 **Small area** (less than 50 m²)"
                        elif superficie < 100:
                            analisis += "\n📏 **Medium area** (50-100 m²)"
                        elif superficie < 200:
                            analisis += "\n📏 **Large area** (100-200 m²)"
                        else:
                            analisis += "\n📏 **Very large area** (more than 200 m²)"
                    else:  # catalán
                        if superficie < 50:
                            analisis += "\n📏 **Superfície petita** (menys de 50 m²)"
                        elif superficie < 100:
                            analisis += "\n📏 **Superfície mitjana** (50-100 m²)"
                        elif superficie < 200:
                            analisis += "\n📏 **Superfície àmplia** (100-200 m²)"
                        else:
                            analisis += "\n📏 **Superfície molt àmplia** (més de 200 m²)"

        except Exception as e:
            log_failure(
                logger,
                logging.WARNING,
                self.settings.log_sensitive_data,
                "Error generando análisis automático",
                e,
            )

        return analisis

    def _construir_prompt(self, datos: CatastroResponse, idioma: str) -> str:
        """Construye el prompt para OpenAI"""
        prompt = "Analiza los siguientes datos catastrales y genera un resumen profesional:\n\n"
        prompt += f"Referencia catastral: {datos.referencia_catastral}\n"

        if datos.datos_basicos:
            if datos.datos_basicos.uso:
                prompt += f"Uso: {datos.datos_basicos.uso}\n"
            if datos.datos_basicos.superficie_construida:
                prompt += f"Superficie construida: {datos.datos_basicos.superficie_construida} m²\n"
            if datos.datos_basicos.antiguedad:
                prompt += f"Año de construcción: {datos.datos_basicos.antiguedad}\n"

        if datos.direccion and datos.direccion.via:
            prompt += f"Dirección: {datos.direccion.via}"
            if datos.direccion.numero:
                prompt += f", {datos.direccion.numero}"
            prompt += "\n"

        prompt += (
            f"\nGenera un resumen en {idioma} que sea útil para un informe técnico profesional."
        )

        return prompt

    def _get_system_prompt(self, idioma: str) -> str:
        """Obtiene el prompt del sistema según el idioma"""
        prompts = {
            "es": "Eres un experto en análisis de datos catastrales de España. Genera resúmenes claros, profesionales y concisos para informes técnicos de inmuebles.",
            "en": "You are an expert in Spanish cadastral data analysis. Generate clear, professional and concise summaries for technical real estate reports.",
            "ca": "Ets un expert en anàlisi de dades cadastrals d'Espanya. Genera resums clars, professionals i concisos per a informes tècnics d'immobles.",
        }

        return prompts.get(idioma, prompts["es"])
