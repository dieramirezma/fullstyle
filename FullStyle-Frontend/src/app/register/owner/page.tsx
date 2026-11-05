import RegisterNavBar from '@/components/register-nav-bar'
import RegisterOwnerForm from '@/features/auth/components/RegisterOwnerForm'

export default function registerClientPage() {
  return (
    <div>
      <RegisterNavBar />
      <div className="h-full flex items-center place-content-around px-10 my-3">
        <RegisterOwnerForm></RegisterOwnerForm>
      </div>
    </div>
  )
}
