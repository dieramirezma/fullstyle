import Image from 'next/image'
import RegisterNavBar from '@/components/register-nav-bar'
import EditCustomerForm from '@/components/edit-customer-form'

export default function registerClientPage() {
  return (
    <div>
      <RegisterNavBar />
      <div className="h-full flex items-stretch justify-center px-20 gap-16">
        <div className="flex-1 max-w-[50%] flex items-center">
          <Image
            src="/images/login.png"
            alt="Login"
            width={600}
            height={500}
            className="rounded-xl h-full object-cover"
          />
        </div>
        <div className="w-[400px] flex items-center">
          <EditCustomerForm />
        </div>
      </div>
    </div>
  )
}
