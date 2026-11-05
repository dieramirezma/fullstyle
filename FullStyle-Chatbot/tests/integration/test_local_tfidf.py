#!/usr/bin/env python3
"""
Script de prueba para verificar que el servicio TF-IDF local funciona correctamente
con el modelo descargado desde Colab.
"""

import logging
import os
import sys

# Configurar logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Añadir el directorio raíz al path para importar los módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_tfidf_service():
    """Prueba el servicio TF-IDF local."""

    print("=== PRUEBA DEL SERVICIO TF-IDF LOCAL ===\n")

    try:
        from app.services.minimal_tfidf_service import minimal_tfidf_service

        # Verificar que el servicio está listo
        print("1. Verificando estado del servicio...")
        if not minimal_tfidf_service.is_ready():
            print("❌ ERROR: El servicio TF-IDF no está listo")
            print(
                "   - Asegúrate de que el archivo 'models/tfidf_vectorizer_only.pkl' existe"
            )
            print("   - Descarga el modelo desde Colab si no lo has hecho")
            return False

        print("✅ Servicio TF-IDF listo")
        print(f"   - Dimensiones: {minimal_tfidf_service.get_embedding_dimensions()}")

        # Probar generación de embeddings con las mismas queries que funcionaron en Colab
        test_queries = [
            "FullStyle plataforma gestión barberías",
            "reserva servicio trabajador",
            "horarios atención salón",
            "cancelación cita política",
            "Qué es FullStyle",
        ]

        print("\n2. Probando generación de embeddings...")

        all_successful = True
        for i, query in enumerate(test_queries, 1):
            print(f"\n   Query {i}: '{query}'")

            embedding = minimal_tfidf_service.get_query_embedding(query)

            if embedding is None:
                print("   ❌ ERROR: No se pudo generar embedding")
                all_successful = False
                continue

            # Validar embedding
            non_zero_count = sum(1 for x in embedding if x != 0)
            embedding_sum = sum(embedding)

            print("   ✅ Embedding generado:")
            print(f"      - Dimensión: {len(embedding)}")
            print(f"      - Valores no-cero: {non_zero_count}")
            print(f"      - Suma total: {embedding_sum:.6f}")
            print(f"      - Muestra: {embedding[:5]}")

            # Validaciones básicas
            if len(embedding) != minimal_tfidf_service.get_embedding_dimensions():
                print("   ⚠️  ADVERTENCIA: Dimensión incorrecta")
                all_successful = False

            if non_zero_count == 0:
                print("   ⚠️  ADVERTENCIA: Embedding vacío (todos ceros)")
                all_successful = False

        print("\n3. Resultado de las pruebas:")
        if all_successful:
            print("✅ Todas las pruebas pasaron exitosamente")
            print("   El servicio TF-IDF local está funcionando correctamente")
            return True
        else:
            print("❌ Algunas pruebas fallaron")
            return False

    except ImportError as e:
        print(f"❌ ERROR de importación: {e}")
        print("   Verifica que el módulo app.services.minimal_tfidf_service existe")
        return False
    except Exception as e:
        print(f"❌ ERROR inesperado: {e}")
        return False


def test_mongodb_compatibility():
    """Prueba la compatibilidad con MongoDB usando variables de entorno."""

    print("\n=== PRUEBA DE COMPATIBILIDAD CON MONGODB ===\n")

    try:
        from app.core.config import settings
        from app.repositories.knowledge_repository import MongoKnowledgeRepository
        from app.services.minimal_tfidf_service import minimal_tfidf_service

        if not minimal_tfidf_service.is_ready():
            print("⚠️  SALTANDO: Servicio TF-IDF no está listo")
            return True

        print("1. Conectando a MongoDB...")

        try:
            knowledge_repo = MongoKnowledgeRepository(
                mongo_uri=settings.MONGO_URI,
                database_name=settings.MONGO_DATABASE_NAME,
                collection_name=settings.MONGO_KB_COLLECTION_NAME,
            )
            print("✅ Conexión a MongoDB exitosa")
        except Exception as e:
            print(f"❌ ERROR conectando a MongoDB: {e}")
            print("   Verifica las variables de entorno MONGO_URI, etc.")
            return False

        print("\n2. Probando búsqueda vectorial...")

        query = "Qué es FullStyle"
        print(f"   Query: '{query}'")

        # Generar embedding
        query_embedding = minimal_tfidf_service.get_query_embedding(query)
        if not query_embedding:
            print("❌ ERROR: No se pudo generar embedding para la query")
            return False

        print(f"   ✅ Embedding generado (dimensión: {len(query_embedding)})")

        # Hacer búsqueda en MongoDB
        try:
            results = knowledge_repo.find_similar_entries(query_embedding, top_k=3)

            if results:
                print(f"   ✅ Búsqueda exitosa: {len(results)} resultados encontrados")
                for i, doc in enumerate(results[:2], 1):
                    score = doc.get("score", 0)
                    text = doc.get("text_chunk", "")[:60]
                    print(f"      {i}. Score: {score:.4f} - {text}...")
                return True
            else:
                print("   ⚠️  Sin resultados encontrados")
                print(
                    "      Verifica que hay datos en MongoDB y el índice vectorial está configurado"
                )
                return False

        except Exception as e:
            print(f"   ❌ ERROR en búsqueda vectorial: {e}")
            return False

    except ImportError as e:
        print(f"❌ ERROR de importación: {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR inesperado: {e}")
        return False


if __name__ == "__main__":
    print("🧪 INICIANDO PRUEBAS DEL SISTEMA TF-IDF LOCAL\n")

    # Verificar que existe el archivo del modelo
    model_path = "models/tfidf_vectorizer_only.pkl"
    if not os.path.exists(model_path):
        print(f"❌ ERROR: No se encontró el modelo en {model_path}")
        print("📥 PASOS PARA SOLUCIONAR:")
        print("   1. Ejecuta todo el código corregido en Colab")
        print("   2. Descarga el archivo 'tfidf_vectorizer_only.pkl'")
        print("   3. Colócalo en la carpeta 'models/' de este proyecto")
        print("   4. Ejecuta este script nuevamente")
        sys.exit(1)

    # Ejecutar pruebas
    success1 = test_tfidf_service()
    success2 = test_mongodb_compatibility()

    print("\n🎯 RESUMEN FINAL:")
    print(f"   - Servicio TF-IDF: {'✅ FUNCIONANDO' if success1 else '❌ FALLA'}")
    print(f"   - MongoDB: {'✅ FUNCIONANDO' if success2 else '❌ FALLA'}")

    if success1 and success2:
        print("\n🎉 ¡SISTEMA COMPLETAMENTE FUNCIONAL!")
        print("   Puedes proceder con el despliegue a Cloud Run")
    else:
        print("\n⚠️  Hay problemas que resolver antes del despliegue")

    sys.exit(0 if (success1 and success2) else 1)
