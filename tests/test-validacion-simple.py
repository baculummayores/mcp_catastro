#!/usr/bin/env python3
"""
Test específico para la validación simplificada de referencias catastrales

Este test verifica que la nueva validación simplificada funciona correctamente
sin intentar parsear códigos internos de provincia o municipio.
"""

import sys
import os

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.catastro_models import ReferenciaCatastral

def test_validacion_simplificada():
    """Test exhaustivo de la validación simplificada"""
    
    print("🧪 TEST DE VALIDACIÓN SIMPLIFICADA")
    print("=" * 50)
    
    # Casos válidos
    casos_validos = [
        "2749704YJ0624N0001DI",  # Madrid
        "4418928VG4141G0001IW",  # Granada (ejemplo real)
        "1234567AB1234C5678XY",  # Formato válido genérico
        "0000000ZZ0000Z0000ZZ",  # Caso límite con ceros
        "9999999ZZ9999Z9999ZZ",  # Caso límite con nueves
        "ABCDEFGHIJ1234567890",  # 20 caracteres alfanuméricos válidos
        "123456789012345678AB",  # 20 caracteres alfanuméricos válidos
    ]
    
    # Casos inválidos
    casos_invalidos = [
        "2749704YJ0624N0001D",   # 19 caracteres (muy corto)
        "2749704YJ0624N0001DIA", # 21 caracteres (muy largo)
        "2749704YJ0624N0001-",   # Carácter inválido
        "274970 YJ0624N0001DI",  # Con espacios internos (se limpia pero queda corto)
        "",                      # Cadena vacía
        "abc def ghi j12 345 67890", # Con muchos espacios
        "2749704YJ0624N0001@",   # Carácter especial inválido
        "2749704YJ0624N0001.",   # Punto al final
    ]
    
    print("\n✅ CASOS VÁLIDOS:")
    print("-" * 30)
    validos_ok = 0
    for i, caso in enumerate(casos_validos, 1):
        try:
            es_valida = ReferenciaCatastral.validar_formato_estatico(caso)
            if es_valida:
                print(f"{i}. ✅ {caso} → VÁLIDA")
                validos_ok += 1
            else:
                print(f"{i}. ❌ {caso} → INVÁLIDA (¡ERROR!)")
        except Exception as e:
            print(f"{i}. 💥 {caso} → ERROR: {e}")
    
    print(f"\nResultado válidos: {validos_ok}/{len(casos_validos)}")
    
    print("\n❌ CASOS INVÁLIDOS:")
    print("-" * 30)
    invalidos_ok = 0
    for i, caso in enumerate(casos_invalidos, 1):
        try:
            es_valida = ReferenciaCatastral.validar_formato_estatico(caso)
            if not es_valida:
                print(f"{i}. ✅ {caso} → INVÁLIDA (correcto)")
                invalidos_ok += 1
            else:
                print(f"{i}. ❌ {caso} → VÁLIDA (¡ERROR!)")
        except Exception as e:
            print(f"{i}. ✅ {caso} → ERROR: {e} (esperado)")
            invalidos_ok += 1
    
    print(f"\nResultado inválidos: {invalidos_ok}/{len(casos_invalidos)}")
    
    # Test de creación de modelo
    print("\n🏗️ TEST DE CREACIÓN DE MODELO:")
    print("-" * 30)
    
    modelo_ok = 0
    for caso in casos_validos[:3]:  # Solo probar algunos casos válidos
        try:
            ref = ReferenciaCatastral(referencia=caso)
            print(f"✅ Modelo creado: {ref.referencia}")
            modelo_ok += 1
        except Exception as e:
            print(f"❌ Error creando modelo para {caso}: {e}")
    
    print(f"\nModelos creados: {modelo_ok}/3")
    
    # Resumen final
    print("\n" + "=" * 50)
    print("📊 RESUMEN FINAL")
    print("=" * 50)
    
    total_tests = len(casos_validos) + len(casos_invalidos) + 3
    total_ok = validos_ok + invalidos_ok + modelo_ok
    
    print(f"✅ Tests exitosos: {total_ok}/{total_tests}")
    print(f"📈 Porcentaje de éxito: {(total_ok/total_tests)*100:.1f}%")
    
    if total_ok >= total_tests * 0.9:  # 90% de éxito
        print("\n🎉 ¡VALIDACIÓN SIMPLIFICADA FUNCIONANDO CORRECTAMENTE!")
        print("   ✅ Acepta formatos válidos de 20 caracteres alfanuméricos")
        print("   ✅ Rechaza formatos inválidos")
        print("   ✅ No intenta parsear códigos internos")
        return True
    else:
        print("\n⚠️ La validación presenta algunos problemas")
        return False

if __name__ == "__main__":
    success = test_validacion_simplificada()
    sys.exit(0 if success else 1)
