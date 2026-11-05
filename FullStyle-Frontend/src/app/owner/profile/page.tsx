'use client'

import { Mail, User2 } from 'lucide-react'
import { useSession } from 'next-auth/react'
import ProfilePasswordForm from '@/features/profile/components/ProfilePasswordForm'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
export default function ProfilePage() {
  const { data: session } = useSession()
  return (
    <div className="space-y-6">
      <h1 className="title tracking-tight">Mi Perfil</h1>

      <div className="grid gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Información Personal</CardTitle>
            <CardDescription>Información básica de tu cuenta</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center space-x-4 rounded-lg border p-4">
              <User2 className="h-5 w-5 text-muted-foreground" />
              <div className="space-y-1">
                <p className="text-sm font-medium leading-none">Nombre</p>
                <p className="text-sm text-muted-foreground">
                  {session?.user.name}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-4 rounded-lg border p-4">
              <Mail className="h-5 w-5 text-muted-foreground" />
              <div className="space-y-1">
                <p className="text-sm font-medium leading-none">Email</p>
                <p className="text-sm text-muted-foreground">
                  {session?.user.email}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <ProfilePasswordForm user={session?.user} />
      </div>
    </div>
  )
}
