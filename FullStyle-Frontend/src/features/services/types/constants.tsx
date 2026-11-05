import PaymentIcon from '../../../components/icons/payment-icon'
import EmployeesIcon from '../../../components/icons/employees-icon'
import { RankingIcon } from '../../../components/icons/ranking-icon'
import AppointmentIcon from '../../../components/icons/appointment-icon'

export const DURATIONOPTIONS = [
  { value: '30', label: '30 minutos' },
  { value: '60', label: '1 hora' },
  { value: '90', label: '1 hora y 30 minutos' },
  { value: '120', label: '2 horas' },
  { value: '150', label: '2 horas y 30 minutos' },
  { value: '180', label: '3 horas' },
]

export const SERVICES = [
  {
    icon: <EmployeesIcon />,
    title: 'Gestión de empleados',
  },
  {
    icon: <AppointmentIcon />,
    title: 'Agenda de citas para clientes',
  },
  {
    icon: <PaymentIcon />,
    title: 'Sistema de pagos integrado',
  },
  {
    icon: <RankingIcon />,
    title: 'Visibilidad de tu negocio',
  },
]
