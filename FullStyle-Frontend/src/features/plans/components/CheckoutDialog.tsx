import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import WidgetWompi from '@/components/widget-wompi'
import { Separator } from '@/components/ui/separator'
import { type Plan } from '@/features/plans/types/types'

const CheckoutDialog = ({
  plan,
  isOpen,
  onClose,
}: {
  plan: Plan | null
  isOpen: boolean
  onClose: () => void
}) => {
  if (!plan) return null

  const priceNumber = plan.price.replace(/[^0-9]/g, '')
  const subtotal = parseInt(priceNumber)
  const discount = 0
  const total = subtotal - discount

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl pointer-events-auto">
        <DialogHeader>
          <DialogTitle>Resumen de la Orden</DialogTitle>
        </DialogHeader>
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="font-medium">Plan {plan.title}</h3>
              <p className="text-sm text-muted-foreground">Facturación anual</p>
            </div>
            <p className="font-medium">
              ${subtotal.toLocaleString()}
              {plan.title.toLowerCase() === 'prueba' ? '/mes' : '/año'}
            </p>
          </div>

          <Separator />

          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Subtotal</span>
              <span>${subtotal.toLocaleString()}</span>
            </div>
            {discount > 0 && (
              <div className="flex justify-between text-sm text-green-600">
                <span>Descuento anual (20%)</span>
                <span>-${discount.toLocaleString()}</span>
              </div>
            )}
            <Separator />
            <div className="flex justify-between font-medium">
              <span>Total</span>
              <span>${total.toLocaleString()}</span>
            </div>
          </div>

          <div className="pt-4">
            <WidgetWompi
              amount={parseInt(priceNumber)}
              isOpen={isOpen}
              label="Pagar suscripción"
              onClose={onClose}
              paymentType="SUB"
              itemId={plan.title}
            />
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}

export default CheckoutDialog
