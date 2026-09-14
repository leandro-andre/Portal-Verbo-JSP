import { z } from 'zod'

export const stockItemSchema = z.object({
  name: z.string().trim().min(1, 'Informe o nome do item.'),
  category_id: z.coerce.number().int().positive('Selecione uma categoria.'),
  unit: z.string().trim().min(1, 'Selecione uma unidade.'),
  minimum_stock: z.coerce.number().int('Informe um numero inteiro.').min(0, 'O estoque minimo nao pode ser negativo.'),
  notes: z.string().trim(),
  is_active: z.boolean(),
})

export type StockItemFormValues = z.input<typeof stockItemSchema>
export type StockItemFormData = z.output<typeof stockItemSchema>

export const stockItemDefaultValues: StockItemFormValues = {
  name: '',
  category_id: 0,
  unit: '',
  minimum_stock: 0,
  notes: '',
  is_active: true,
}
