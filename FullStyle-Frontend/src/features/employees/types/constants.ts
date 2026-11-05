export const DAYS = [
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday',
  'Sunday',
]

export const SCHEDULE = DAYS.reduce(
  (acc, day) => ({
    ...acc,
    [day]: { startTime: '10:00', endTime: '19:00' },
  }),
  {},
)
