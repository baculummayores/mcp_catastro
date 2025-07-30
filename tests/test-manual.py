#!/usr/bin/env python3
"""
Test manual directo - Prueba los servicios sin protocolo MCP

ACTUALIZACIONES V2:
- Validación simplificada de referencias catastrales (solo formato básico)
- Múltiples casos de prueba para validación
- Uso de referencia real de Granada como ejemplo
- Eliminado el parseo complejo de códigos de provincia
"""

import asyncio
import sys
import os

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.catastro_service import CatastroService
from services.ai_summary import AIService
from models.catastro_models import ReferenciaCatastral

async def test_direct_services():
    """Prueba directa de los servicios sin MCP"""
    
    print("🧪 PRUEBA DIRECTA DE SERVICIOS")
    print("=" * 40)
    
    # Inicializar servicios
    catastro_service = CatastroService()
    ai_service = AIService()
    
    # Test 1: Validación de referencia
    print("\n1️⃣ Test de validación de referencia:")
    test_refs = [
        "2749704YJ0624N0001DI",  # Referencia válida
        "4418928VG4141G0001IW",  # Referencia de Granada del ejemplo
        "123456789012345678AB",  # Referencia inválida (formato incorrecto)
        "2749704YJ0624N0001D",   # Referencia corta (19 caracteres)
    ]
    
    for ref_test in test_refs:
        es_valida = ReferenciaCatastral.validar_formato_estatico(ref_test)
        print(f"   Referencia: {ref_test}")
        print(f"   Válida: {'✅ SÍ' if es_valida else '❌ NO'}")
        print()
    
    # Test 2: Consulta por referencia (usando la referencia de Granada)
    print("\n2️⃣ Test de consulta por referencia:")
    ref_consulta = "4418928VG4141G0001IW"  # Referencia de Granada del ejemplo
    try:
        resultado = await catastro_service.consultar_por_referencia(ref_consulta)
        print(f"   Referencia: {ref_consulta}")
        print(f"   Estado: {resultado.estado_consulta}")
        if resultado.datos_basicos:
            print(f"   Uso: {resultado.datos_basicos.uso}")
            print(f"   Superficie: {resultado.datos_basicos.superficie_construida} m²")
        if resultado.direccion:
            print(f"   Dirección: {resultado.direccion.via} {resultado.direccion.numero}")
            print(f"   Municipio: {resultado.direccion.municipio}")
            print(f"   Provincia: {resultado.direccion.provincia}")
        print("   ✅ Consulta exitosa")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test 3: Consulta por coordenadas
    print("\n3️⃣ Test de consulta por coordenadas:")
    try:
        lat, lon = 40.4168, -3.7038
        resultado = await catastro_service.consultar_por_coordenadas(lat, lon)
        print(f"   Coordenadas: {lat}, {lon}")
        print(f"   Estado: {resultado.estado_consulta}")
        print(f"   Referencia encontrada: {resultado.referencia_catastral}")
        print("   ✅ Consulta exitosa")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test 4: Resumen IA
    print("\n4️⃣ Test de resumen IA:")
    try:
        resumen = await ai_service.generar_resumen(ref_consulta, usar_openai=False, idioma="es")
        print(f"   Referencia: {ref_consulta}")
        print(f"   Resumen generado: {len(resumen)} caracteres")
        print(f"   Inicio: {resumen[:100]}...")
        print("   ✅ Resumen generado")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    print("\n" + "=" * 40)
    print("🎉 Pruebas directas completadas")
    print("Si ves ✅ en la mayoría, los servicios funcionan bien")

if __name__ == "__main__":
    asyncio.run(test_direct_services())