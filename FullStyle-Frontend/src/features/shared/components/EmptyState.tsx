import { ArrowRight } from 'lucide-react'
import Link from 'next/link'
import { buttonVariants } from '@/components/ui/button'

interface EmptyStateProps {
  icon: React.ReactNode
  title: string
  description: string
  actionHref?: string
  actionLabel?: string
  children?: React.ReactNode
}

const EmptyState = ({
  icon,
  title,
  description,
  actionHref,
  actionLabel,
  children,
}: EmptyStateProps) => {
  return (
    <div className="container mx-auto max-w-4xl w-full">
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="p-8 sm:p-12">
          <div className="flex justify-center mb-8">
            <div className="relative">
              <div className="w-24 h-24 rounded-full bg-primary/10 flex items-center justify-center">
                {icon}
              </div>
              <span className="absolute -bottom-1 -right-1 flex h-8 w-8 items-center justify-center rounded-full bg-primary text-white">
                <ArrowRight className="h-4 w-4" />
              </span>
            </div>
          </div>
          <div className="space-y-6 max-w-lg mx-auto text-center">
            <h1 className="title">{title}</h1>
            <p className="text-gray-500 text-lg">{description}</p>
            <div className="h-px bg-gradient-to-r from-transparent via-gray-200 to-transparent my-8" />
            {actionHref && actionLabel && (
              <Link
                href={actionHref}
                className={buttonVariants({ variant: 'default' })}
              >
                {actionLabel}
              </Link>
            )}
            {children && (
              <div className="bg-gray-50 rounded-lg text-left mt-8">
                {children}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default EmptyState
