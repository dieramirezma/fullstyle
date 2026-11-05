# Contratos aditivos del cierre complementario

Todos los paths REST siguientes usan el prefijo `/api` de negocio; por el proxy son `/business/api/…` o `/api/logic/…`. Se conservan REST, GraphQL, Go, Flask, NextAuth y Firebase. No se agregan credenciales comerciales. La verificación actual se registra en [el checklist](refactoring-plan.md).

| Método / ruta | Identidad y autorización | Efecto / contrato |
| --- | --- | --- |
| POST `/mfa/recover` | Contraseña SQL actual + código offline; sin bearer | Consume todos los códigos, elimina autenticador y revoca sesiones; 401 uniforme al rechazar |
| POST `/mfa/recovery-codes` | Bearer vigente, contraseña y OTP fresco | Reemplaza diez códigos; solo hashes en SQL |
| POST `/verify-2fa` | Contrato previo de confirmación | Añade `recovery_codes`; conserva `message` y HTTP 200 |
| POST `/refresh` | Refresh firmado, identidad activa y epoch/MFA válidos | Consumo único; `Idempotency-Key` opcional de 64 hex permite recuperar el mismo par durante 15 s; nunca un sucesor revocado |
| DELETE `/logout` | Access o refresh firmado no expirado, identidad/política vigentes | Revoca familia y JTI de forma idempotente; puede usar un refresh consumido para cerrar sus descendientes |
| GET/DELETE `/payment/intents/<reference>` | Cliente de la reserva o dueño de la sede | Estado/vencimiento; DELETE cancela intención y reserva pendiente; 409 si requiere reembolso |
| GET `/payment/quote/<appointment_id>` | Cliente de la reserva o dueño de la sede | Precio inmutable guardado para iniciar el pago desde la interfaz; rechaza reservas cerradas y términos heredados sin revisar |
| GET `/payment/reconciliation?site_id=<id>` | Dueño de la sede | Libro de transacciones y resolución, sin payloads de proveedor |
| POST `/payment/refunds/<transaction_id>` | Dueño de la sede, `reason` y `operation_id` | Solo cargos aprobados verificados; efecto sintético, atómico y deduplicado; no elimina auditoría |
| GET `/subscriptions/catalog` | Bearer activo + entorno sintético | Catálogo ficticio del servidor |
| GET/POST `/subscriptions` | Manager dueño de su cuenta + entorno sintético | Lista propia / intención pendiente; precio/estado no aceptan sobreescritura del cliente |
| POST `/local/payments/simulate` | Propiedad de referencia y entorno sintético exacto | Genera aprobación local con importe/moneda SQL e identificador determinista por operación; no llama a un proveedor |
| GET `/mail/events` | Bearer activo y destinatario SQL del evento | Estado y errores de los últimos 100 eventos propios, sin cuerpos ni enlaces de recuperación |
| POST `/mail/events/<event_id>/retry` | Destinatario SQL, `reason` y `operation_id` | Reprograma contacto local válido, nunca una entrega ya registrada ni un payload desconocido |

El simulador es un adaptador de pruebas explícito: no suplanta una verificación comercial. El webhook externo conserva checksum y capacidad de servicio ligada al cuerpo. La coincidencia de referencia, moneda e importe se exige también para las suscripciones. El pago aprobado después del cierre se registra como `review`, sin reservar de nuevo un horario que otra persona ya podría ocupar.

## Chat y Next

| Método / entrada | Autorización | Resultado |
| --- | --- | --- |
| GET `/chatbot/api/v1/chat/history/<session>` | Identidad delegada verificada por negocio | Últimos 50 turnos propios; agrega nota/fecha de revisión |
| POST `/chatbot/api/v1/chat/history/<session>/operations/<operation>/review` | Misma identidad; confirmación `checked_booking_state: true` y nota | Excluye operación activa mediante lock por conversación; marca `reviewed`; `reexecuted: false` |
| `/login` | Contraseña + OTP o recuperación explícita | Recuperación no inicia sesión automáticamente ni omite la contraseña |
| `/operations` | UI usa la sesión SQL; cada operación autoriza en negocio | Reservas, intenciones, conciliación, suscripción sintética y revisión de correo |
| `/chatbot` | Sesión SQL activa | Recupera conversación por identificador y permite revisar resultados inciertos |

Las rutas y campos GraphQL existentes permanecen. Go añade `session_family` al par de tokens; Flask conserva la misma familia durante renovaciones. Una sesión sin familia sigue siendo compatible y usa su JTI como raíz al renovarse. Los claims de roles no sustituyen la autorización SQL.

## Datos y rollback

La migración `0005_local_completion` es aditiva. Introduce códigos hash, respuestas de renovación cifradas y de vida corta, estados/vencimiento de intenciones, auditoría financiera, suscripciones sintéticas y metadatos de revisión/retención. Inicializa la resolución de pagos ya aplicados, sin reevaluar precios ni modificar contraseñas.

La retención sustituye únicamente contenido de turnos completados/revisados que superan 30 días. Conserva hash del mensaje para detectar reutilización del ID con otro contenido. No convierte turnos inciertos en éxito ni borra su evidencia automáticamente.

Readiness requiere `0005_local_completion`. Las imágenes de fase 6 no verifican familias de sesión y no constituyen un rollback autorizado para cuentas que ya usan este contrato. Conservar esquema, claves y validadores actuales al reconstruir una versión compatible; no restablecer una política de revocación anterior.
