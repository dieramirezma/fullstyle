export const SubscriptionConfirmationEmail: React.FC<
  Readonly<{
    ownerName: string
    subscriptionPlan: string
    paymentDate: string
    finishDate: string
  }>
> = ({ ownerName, subscriptionPlan, paymentDate, finishDate }) => (
  <div
    style={{
      fontFamily: 'Arial, sans-serif',
      maxWidth: '600px',
      margin: '0 auto',
      padding: '20px',
      border: '1px solid #ddd',
      borderRadius: '8px',
      backgroundColor: '#f9f9f9',
      textAlign: 'left',
    }}
  >
    <h2 style={{ color: '#28a745', textAlign: 'center' }}>
      🎉 ¡Bienvenido a FullStyle!
    </h2>
    <p>
      Hola <strong>{ownerName}</strong>,
    </p>
    <p>
      Nos alegra darte la bienvenida a FullStyle. Has completado con éxito el
      pago de tu suscripción y ahora tu perfil está activo en nuestra
      plataforma.
    </p>

    <div
      style={{
        backgroundColor: '#fff',
        padding: '15px',
        borderRadius: '8px',
        border: '1px solid #ddd',
      }}
    >
      <h3 style={{ marginBottom: '5px', color: '#28a745' }}>
        Detalles de tu Suscripción
      </h3>

      <hr style={{ margin: '10px 0' }} />

      <p>
        <strong>📅 Fecha de pago:</strong> {paymentDate}
      </p>
      <p>
        <strong>📋 Plan seleccionado:</strong> {subscriptionPlan}
      </p>
      <p>
        <strong>📅 Fecha de renovacion:</strong> {finishDate}
      </p>

      <hr style={{ margin: '10px 0' }} />

      <p>Puedes gestionar tu negocio desde tu panel de administración:</p>
      <p style={{ textAlign: 'center' }}>
        <a
          href="https://full-style.com/owner"
          style={{
            display: 'inline-block',
            padding: '10px 15px',
            backgroundColor: '#007bff',
            color: '#fff',
            textDecoration: 'none',
            borderRadius: '5px',
            fontWeight: 'bold',
          }}
        >
          Ir al Panel de Control
        </a>
      </p>
    </div>

    <p style={{ fontSize: '14px', color: '#666', marginTop: '20px' }}>
      Si tienes alguna pregunta, no dudes en contactarnos.
    </p>

    <p
      style={{
        fontSize: '16px',
        fontWeight: 'bold',
        color: '#007bff',
        textAlign: 'center',
      }}
    >
      — El equipo de FullStyle
    </p>
  </div>
)
