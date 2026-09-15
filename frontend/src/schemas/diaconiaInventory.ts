import { z } from 'zod'

export const inventoryItemSchema = z.object({
  name: z.string().trim().min(1, 'Informe o nome do item.'),
  category_id: z.coerce.number().int().positive('Selecione uma categoria.'),
  description: z.string().trim(),
  is_active: z.boolean(),
})

export type InventoryItemFormValues = z.input<typeof inventoryItemSchema>
export type InventoryItemFormData = z.output<typeof inventoryItemSchema>

export const inventoryItemDefaultValues: InventoryItemFormValues = {
  name: '',
  category_id: 0,
  description: '',
  is_active: true,
}
