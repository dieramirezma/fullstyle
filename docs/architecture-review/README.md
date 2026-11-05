# Revisión de arquitectura

Alcance: orquestación y ocho componentes FullStyle. Se conserva la arquitectura de servicios y se corrigen seguridad, contratos, consistencia y operación antes de considerar separaciones adicionales. `fullstyle-rewrite` no forma parte de este monorepo.

La línea base de importación, commits y autores se registran en [provenance.json](../provenance.json). Este registro contiene hashes anteriores al saneamiento y a las adaptaciones de portabilidad; no equivale al fingerprint de validación del monorepo.

La metodología combina revisión de rutas, análisis estático, pruebas con persistencia real aislada, fallos controlados y mutaciones que deben detectar regresiones. Las mediciones y pruebas son locales y sintéticas. No se infiere la configuración de producción a partir de estos manifiestos.

- [Arquitectura actual](current-architecture.md)
- [Hallazgos](findings.md)
- [Decisiones de arquitectura](target-architecture.md)
- [Plan y checklist por fase](refactoring-plan.md)
- [Migración y validación](migration-and-validation.md)
- [Comparación](comparison.md)
- [Contratos aditivos](additional-contracts.md)
- [Matriz base de rutas](route-matrix.json)

La validación de la publicación se mantiene en [monorepo-migration.md](../monorepo-migration.md). La operación y reproducción están en [local-demo.md](../local-demo.md) y [testing.md](../testing.md).
