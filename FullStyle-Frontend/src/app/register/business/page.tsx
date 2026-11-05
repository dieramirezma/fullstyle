import RegisterNavBar from '@/components/register-nav-bar'
import RegisterBusinessForm from '@/features/business/components/RegisterBusinessForm'

export default function registerClientPage() {
  return (
    <div>
      <RegisterNavBar />
      <div className="h-full flex place-content-center pb-20 pt-10 px-10">
        <RegisterBusinessForm></RegisterBusinessForm>
      </div>
    </div>
  )
}
