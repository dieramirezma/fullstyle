import RegisterNavBar from '@/components/register-nav-bar'
import RegisterServicesForm from '@/features/services/components/RegisterServicesForm'

export default function registerClientPage() {
  return (
    <div>
      <RegisterNavBar />
      <div className="h-full flex items-center place-content-around p-10">
        <RegisterServicesForm></RegisterServicesForm>
      </div>
    </div>
  )
}
