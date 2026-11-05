import RegisterNavBar from '@/components/register-nav-bar'
import WorkerScheduleForm from '@/features/employees/components/WorkerScheduleForm'

export default function registerClientPage() {
  return (
    <div>
      <RegisterNavBar />
      <div className="h-full flex items-center place-content-around px-10 py-10">
        <WorkerScheduleForm />
      </div>
    </div>
  )
}
