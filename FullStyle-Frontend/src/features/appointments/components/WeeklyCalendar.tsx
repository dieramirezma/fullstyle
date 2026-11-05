'use client'

import {
  fetchSiteDetail,
  fetchWorkerDetail,
  fetchWeeklySchedule,
  fetchServiceDetail,
} from '@/features/appointments/api/appointmentApi'
import { toast } from 'sonner'
import apiClient from '@/utils/apiClient'
import { Button } from '@/components/ui/button'
import { useState, useEffect, useCallback } from 'react'
import {
  ChevronLeft,
  ChevronRight,
  Loader2,
  Calendar,
  Clock,
  CheckCircle2,
  XCircle,
  User,
  MapPin,
  X,
} from 'lucide-react'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

import {
  format,
  addDays,
  startOfWeek,
  endOfWeek,
  parse,
  addMinutes,
  isBefore,
  isAfter,
  isEqual,
  isToday,
  isPast,
} from 'date-fns'
import { es } from 'date-fns/locale'
import type {
  Detail,
  Site,
  AppointmentData,
  TimeSlot,
  WeeklyCalendarProps,
  WeeklySchedule,
  Worker,
} from '../types/types'

export default function WeeklyCalendar({
  workerId,
  siteId,
  serviceId,
  clientId,
  onAppointmentScheduled,
}: WeeklyCalendarProps) {
  // Estados del componente
  const [loading, setLoading] = useState(true)
  const [showConfirmation, setShowConfirmation] = useState(false)
  const [siteDetail, setSiteDetail] = useState<Site[] | null>(null)
  const [weekStart, setWeekStart] = useState(
    startOfWeek(new Date(), { weekStartsOn: 0 }),
  )
  const [schedule, setSchedule] = useState<WeeklySchedule | null>(null)
  const [selectedSlot, setSelectedSlot] = useState<string | null>(null)
  const [workerDetail, setWorkerDetail] = useState<Worker[] | null>(null)
  const [serviceDetail, setServiceDetail] = useState<Detail[] | null>(null)
  const [hoveredSlot, setHoveredSlot] = useState<string | null>(null)

  // Función para cargar todos los datos necesarios
  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      await fetchWeeklyScheduleAPI()
      await fetchServiceDetailAPI()
      await fetchWorkerDetailAPI()
      await fetchSiteDetailAPI()
    } finally {
      setLoading(false)
    }
  }, [weekStart, workerId, siteId, serviceId])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  // Funciones para obtener datos de la API
  const fetchSiteDetailAPI = async () => {
    try {
      const response = await fetchSiteDetail(siteId)
      setSiteDetail(response)
    } catch (error) {
      console.error('Error fetching site detail:', error)
    }
  }

  const fetchWorkerDetailAPI = async () => {
    try {
      const response = await fetchWorkerDetail(workerId)
      setWorkerDetail(response)
    } catch (error) {
      console.error('Error fetching worker detail:', error)
    }
  }

  const fetchWeeklyScheduleAPI = async () => {
    try {
      const response = await fetchWeeklySchedule(workerId, weekStart)
      setSchedule(response)
    } catch (error) {
      console.error('Error fetching schedule:', error)
    }
  }

  const fetchServiceDetailAPI = async () => {
    try {
      const response = await fetchServiceDetail(serviceId, siteId)
      setServiceDetail(response)
    } catch (error) {
      console.error('Error fetching service detail:', error)
    }
  }

  // Navegación entre semanas
  const handlePreviousWeek = () => {
    setWeekStart(addDays(weekStart, -7))
  }

  const handleNextWeek = () => {
    setWeekStart(addDays(weekStart, 7))
  }

  // Generar slots de tiempo de 30 minutos
  const generateTimeSlots = (
    startTime: string,
    endTime: string,
  ): TimeSlot[] => {
    const slots: TimeSlot[] = []
    let current = parse(startTime, 'HH:mm:ss', new Date())
    const end = parse(endTime, 'HH:mm:ss', new Date())

    while (isBefore(current, end)) {
      const next = addMinutes(current, 30)
      if (isAfter(next, end)) break

      slots.push({
        start: format(current, 'HH:mm'),
        end: format(next, 'HH:mm'),
      })
      current = next
    }
    return slots
  }

  // Verificar si un slot está ocupado
  const isSlotOccupied = (
    slot: TimeSlot,
    occupiedSlots: Array<{ start: string; end: string }> | undefined,
  ): boolean => {
    if (!occupiedSlots) return false
    return occupiedSlots.some((occupiedSlot) => {
      const slotStart = parse(slot.start, 'HH:mm', new Date())
      const occupiedStart = parse(occupiedSlot.start, 'HH:mm:ss', new Date())
      const occupiedEnd = parse(occupiedSlot.end, 'HH:mm:ss', new Date())
      return (
        (isEqual(slotStart, occupiedStart) ||
          isAfter(slotStart, occupiedStart)) &&
        isBefore(slotStart, occupiedEnd)
      )
    })
  }

  // Verificar si un slot está en el pasado
  const isSlotInPast = (day: string, slot: TimeSlot): boolean => {
    const dayIndex = [
      'Sunday',
      'Monday',
      'Tuesday',
      'Wednesday',
      'Thursday',
      'Friday',
      'Saturday',
    ].findIndex((d) => d.toLowerCase() === day.toLowerCase())
    const slotDate = addDays(weekStart, dayIndex)
    const slotDateTime = parse(
      `${format(slotDate, 'yyyy-MM-dd')} ${slot.start}`,
      'yyyy-MM-dd HH:mm',
      new Date(),
    )
    return isPast(slotDateTime)
  }

  // Manejar clic en un slot de tiempo (versión simplificada para pruebas)
  const handleSlotClick = (day: string, slot: TimeSlot) => {
    // Verificar disponibilidad básica
    if (
      !schedule ||
      isSlotOccupied(slot, schedule.schedule[day].occupied) ||
      isSlotInPast(day, slot)
    ) {
      return
    }

    const dayIndex = [
      'Sunday',
      'Monday',
      'Tuesday',
      'Wednesday',
      'Thursday',
      'Friday',
      'Saturday',
    ].findIndex((d) => d.toLowerCase() === day.toLowerCase())
    const slotDate = addDays(weekStart, dayIndex)
    const formattedSlot = `${format(slotDate, 'yyyy-MM-dd')}T${slot.start}`

    // Simplemente establecer el slot seleccionado y mostrar la confirmación
    setSelectedSlot(formattedSlot)
    setShowConfirmation(true)

    // Notificar al usuario que esta es una versión simplificada para pruebas
    toast.info('Modo de prueba activado', {
      description:
        'Usa el botón "Confirmar reserva directamente" para agendar sin pago',
      duration: 4000,
    })
  }

  // Preparar datos de la cita
  const handleAppointmentData = () => {
    if (!selectedSlot) return null
    const [date, time] = selectedSlot.split('T')
    const appointmentData: AppointmentData = {
      appointmenttime: `${date}T${time}:00`,
      status: 'pending',
      worker_id: workerId,
      site_id: siteId,
      service_id: serviceId,
      client_id: clientId,
      request: true,
    }
    return appointmentData
  }

  // Confirmar la cita (versión simplificada para pruebas)
  const handleConfirmAppointment = async () => {
    const appointmentData = handleAppointmentData()
    if (appointmentData === null) return

    try {
      await apiClient.post('appointment', {
        ...appointmentData,
        request: false,
      })
      toast.success('Reserva pendiente creada', {
        description: 'La reserva sigue pendiente de pago.',
      })
      setShowConfirmation(false)
      onAppointmentScheduled()
    } catch (error) {
      toast.error('No se pudo crear la reserva', {
        description: 'Revisa la disponibilidad y vuelve a intentarlo.',
      })
      console.error('Error al agendar cita:', error)
    }
  }

  // Estados de carga y error
  if (loading) {
    return (
      <div className="flex h-[500px] items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 rounded-xl">
        <div className="text-center space-y-4">
          <Loader2 className="h-12 w-12 animate-spin text-blue-600 mx-auto" />
          <p className="text-blue-700 font-medium">Cargando calendario...</p>
        </div>
      </div>
    )
  }

  if (!schedule) {
    return (
      <div className="flex h-[500px] items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl">
        <div className="text-center space-y-4">
          <Calendar className="h-16 w-16 text-gray-400 mx-auto" />
          <p className="text-gray-600 font-medium">
            No hay calendario disponible
          </p>
        </div>
      </div>
    )
  }

  // Generar todos los slots de tiempo basados en el primer día disponible
  const allTimeSlots = generateTimeSlots(
    schedule.schedule[Object.keys(schedule.schedule)[0]]?.available[0]?.start ||
      '09:00:00',
    schedule.schedule[Object.keys(schedule.schedule)[0]]?.available[0]?.end ||
      '17:00:00',
  )

  return (
    <div className="space-y-6">
      {/* Header con información del servicio */}
      {serviceDetail && workerDetail && siteDetail && (
        <Card className="bg-gradient-to-r from-blue-600 to-purple-600 border-0">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="space-y-2">
                <h2 className="text-2xl font-bold flex items-center gap-2">
                  <Calendar className="h-6 w-6" />
                  {serviceDetail[0]?.service_name}
                </h2>
                <div className="flex items-center gap-4 text-blue-100">
                  <div className="flex items-center gap-1">
                    <User className="h-4 w-4" />
                    <span>{workerDetail[0]?.name}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <MapPin className="h-4 w-4" />
                    <span>{siteDetail[0]?.name}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Clock className="h-4 w-4" />
                    <span>{serviceDetail[0]?.duration} min</span>
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold">
                  ${serviceDetail[0]?.price}
                </div>
                <Badge variant="default">
                  {serviceDetail[0]?.category_name}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Calendario principal */}
      <Card className="shadow-xl border-0 overflow-hidden">
        {/* Header con navegación de semanas */}
        <CardHeader className="bg-gradient-to-r from-gray-50 to-gray-100 border-b">
          <div className="flex items-center justify-between">
            <Button
              variant="outline"
              size="sm"
              onClick={handlePreviousWeek}
              className="hover:bg-blue-50 hover:border-blue-200 transition-colors bg-transparent"
            >
              <ChevronLeft className="h-4 w-4 mr-1" />
              Anterior
            </Button>

            <div className="text-center">
              <h3 className="text-lg font-semibold text-gray-800">
                {format(weekStart, 'MMMM yyyy', { locale: es })}
              </h3>
              <p className="text-sm text-gray-600">
                {format(weekStart, 'd', { locale: es })} -{' '}
                {format(endOfWeek(weekStart), 'd', { locale: es })}
              </p>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={handleNextWeek}
              className="hover:bg-blue-50 hover:border-blue-200 transition-colors bg-transparent"
            >
              Siguiente
              <ChevronRight className="h-4 w-4 ml-1" />
            </Button>
          </div>
        </CardHeader>

        {/* Contenido del calendario */}
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <div style={{ minWidth: '800px' }}>
              {/* Header de días */}
              <div className="flex bg-gradient-to-r from-blue-50 to-purple-50 border-b">
                <div className="w-24 p-4 border-r bg-white flex items-center justify-center">
                  <Clock className="h-5 w-5 text-gray-400" />
                </div>
                {Object.entries(schedule.schedule).map(([day]) => {
                  const dayIndex = [
                    'Sunday',
                    'Monday',
                    'Tuesday',
                    'Wednesday',
                    'Thursday',
                    'Friday',
                    'Saturday',
                  ].findIndex((d) => d.toLowerCase() === day.toLowerCase())
                  const slotDate = addDays(weekStart, dayIndex)
                  const isCurrentDay = isToday(slotDate)

                  return (
                    <div
                      key={day}
                      className={`flex-1 p-4 text-center border-r transition-colors ${
                        isCurrentDay
                          ? 'bg-blue-100 border-blue-200'
                          : 'hover:bg-blue-25'
                      }`}
                      style={{ minWidth: '100px' }}
                    >
                      <div
                        className={`text-sm font-medium ${isCurrentDay ? 'text-blue-700' : 'text-gray-600'}`}
                      >
                        {format(slotDate, 'EEE', { locale: es })}
                      </div>
                      <div
                        className={`text-2xl font-bold mt-1 ${isCurrentDay ? 'text-blue-800' : 'text-gray-800'}`}
                      >
                        {format(slotDate, 'd')}
                      </div>
                      {isCurrentDay && (
                        <Badge
                          variant="secondary"
                          className="mt-1 bg-blue-200 text-blue-800 text-xs"
                        >
                          Hoy
                        </Badge>
                      )}
                    </div>
                  )
                })}
              </div>

              {/* Cuadrícula de horarios */}
              <div className="relative">
                {allTimeSlots.map((slot, timeIndex) => (
                  <div
                    key={timeIndex}
                    className="flex border-b border-gray-100 hover:bg-gray-25 transition-colors"
                  >
                    {/* Columna de tiempo */}
                    <div className="w-24 p-3 border-r bg-gray-50 flex items-center justify-center">
                      <span className="text-sm font-medium text-gray-600">
                        {slot.start}
                      </span>
                    </div>

                    {/* Slots por día */}
                    {Object.entries(schedule.schedule).map(
                      ([day, daySchedule]) => {
                        const isOccupied = isSlotOccupied(
                          slot,
                          daySchedule.occupied,
                        )
                        const isPastSlot = isSlotInPast(day, slot)
                        const slotKey = `${day}-${slot.start}`
                        const isHovered = hoveredSlot === slotKey

                        return (
                          <div
                            key={day}
                            className="flex-1 border-r relative"
                            style={{ minWidth: '100px', minHeight: '60px' }}
                          >
                            <button
                              disabled={isOccupied || isPastSlot}
                              onClick={() => {
                                if (!isOccupied && !isPastSlot) {
                                  handleSlotClick(day, slot)
                                }
                              }}
                              onMouseEnter={() => {
                                if (!isOccupied && !isPastSlot) {
                                  setHoveredSlot(slotKey)
                                }
                              }}
                              onMouseLeave={() => {
                                setHoveredSlot(null)
                              }}
                              className={`w-full h-full p-2 transition-all duration-200 flex items-center justify-center group ${
                                isOccupied
                                  ? 'bg-red-100 cursor-not-allowed'
                                  : isPastSlot
                                    ? 'bg-gray-100 cursor-not-allowed opacity-50'
                                    : 'hover:bg-green-50 hover:shadow-md cursor-pointer transform hover:scale-105'
                              }`}
                              style={{ minHeight: '60px' }}
                            >
                              {isOccupied ? (
                                <div className="flex items-center gap-1 text-red-600">
                                  <XCircle className="h-4 w-4" />
                                  <span className="text-xs font-medium">
                                    Ocupado
                                  </span>
                                </div>
                              ) : isPastSlot ? (
                                <div className="flex items-center gap-1 text-gray-400">
                                  <Clock className="h-4 w-4" />
                                  <span className="text-xs">Pasado</span>
                                </div>
                              ) : (
                                <div
                                  className={`flex items-center gap-1 transition-colors ${
                                    isHovered
                                      ? 'text-green-600'
                                      : 'text-gray-400 group-hover:text-green-600'
                                  }`}
                                >
                                  <CheckCircle2 className="h-4 w-4" />
                                  <span className="text-xs font-medium">
                                    Disponible
                                  </span>
                                </div>
                              )}
                            </button>
                          </div>
                        )
                      },
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Leyenda */}
      <Card className="bg-gray-50 border-gray-200">
        <CardContent className="p-4">
          <div className="flex items-center justify-center gap-6 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-green-100 border border-green-200 rounded flex items-center justify-center">
                <CheckCircle2 className="h-3 w-3 text-green-600" />
              </div>
              <span className="text-gray-600">Disponible</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-red-100 border border-red-200 rounded flex items-center justify-center">
                <XCircle className="h-3 w-3 text-red-600" />
              </div>
              <span className="text-gray-600">Ocupado</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-gray-100 border border-gray-200 rounded flex items-center justify-center">
                <Clock className="h-3 w-3 text-gray-400" />
              </div>
              <span className="text-gray-600">No disponible</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Botón de confirmación directa (para pruebas) */}
      {showConfirmation && selectedSlot && (
        <Card className="p-4 bg-blue-50 border-blue-200">
          <div className="flex flex-col space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-bold text-lg">
                  Reserva directa (para pruebas)
                </h3>
                <p className="text-sm text-gray-500">
                  {format(
                    new Date(selectedSlot),
                    "EEEE, d 'de' MMMM 'a las' HH:mm",
                    { locale: es },
                  )}
                </p>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setShowConfirmation(false)
                }}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>

            <div className="grid gap-4">
              {serviceDetail && (
                <div className="flex justify-between items-center">
                  <span>Servicio: {serviceDetail[0]?.service_name}</span>
                  <span className="font-bold">${serviceDetail[0]?.price}</span>
                </div>
              )}

              {workerDetail && (
                <div className="flex items-center gap-2">
                  <User className="h-4 w-4 text-blue-500" />
                  <span>Profesional: {workerDetail[0]?.name}</span>
                </div>
              )}

              {siteDetail && (
                <div className="flex items-center gap-2">
                  <MapPin className="h-4 w-4 text-blue-500" />
                  <span>Sede: {siteDetail[0]?.name}</span>
                </div>
              )}
            </div>

            <div className="flex justify-end">
              <Button
                onClick={handleConfirmAppointment}
                className="w-full bg-green-600 hover:bg-green-700"
              >
                Confirmar reserva directamente
              </Button>
            </div>
          </div>
        </Card>
      )}
    </div>
  )
}
