import Fullstyle from '@/components/icons/fullstyle'
import RegisterNavBar from '@/components/register-nav-bar'
import EditWorker from '@/features/employees/components/EditWorker'

export default function registerClientPage() {
  return (
    <div>
      <RegisterNavBar />
      <div className="h-full flex items-center place-content-around px-20">
        <Fullstyle />
        <EditWorker></EditWorker>
      </div>
    </div>
  )
}
