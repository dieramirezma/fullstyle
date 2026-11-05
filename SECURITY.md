# Seguridad de la demo

Esta configuración es exclusivamente local y sintética. No utilizar las claves de demostración ni los manifiestos de Compose para producción. Las bases y servicios internos usan una red Docker interna; los puertos publicados se enlazan a `127.0.0.1`.

Las credenciales de proveedores, archivos `.env`, bases, claves de cifrado y respaldos quedan fuera de Git. El monorepo comienza con una importación sin los objetos Git históricos. Los identificadores Firebase de la aplicación se sustituyen por valores ficticios del emulador.

El análisis de secretos usa Gitleaks con reglas predeterminadas y excepciones explícitas para claves sintéticas de tests y artefactos locales no publicados. Se escanean tanto los archivos como el historial nuevo antes de publicar. Este análisis no certifica que credenciales de los repositorios originales hayan sido rotadas; esa operación corresponde a sus titulares.

Para informar una vulnerabilidad, usar el canal privado de seguridad de GitHub si está habilitado. No adjuntar credenciales ni datos personales a un issue público.
