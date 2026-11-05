'use client'

import AddWorkerForm from '@/features/employees/components/AddWorkerForm'
import { type AddWorkerDialogProps } from '@/features/employees/types/types'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

export function AddWorkerDialog({
  siteId,
  services,
  onWorkerAdded,
  open,
  setOpen,
}: AddWorkerDialogProps) {
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Agregar Nuevo Trabajador</DialogTitle>
          <DialogDescription>
            Ingresa los datos del nuevo trabajador y su horario
          </DialogDescription>
        </DialogHeader>
        <AddWorkerForm
          siteId={siteId}
          services={services}
          onWorkerAdded={onWorkerAdded}
          open={open}
          setOpen={setOpen}
        />
      </DialogContent>
    </Dialog>
  )
}
