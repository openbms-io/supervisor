import { cn } from './utils'

describe('utils', () => {
  describe('cn', () => {
    it('should merge class names correctly', () => {
      const result = cn('text-sm', 'font-bold', 'text-red-500')
      expect(result).toContain('text-sm')
      expect(result).toContain('font-bold')
      expect(result).toContain('text-red-500')
    })

    it('should handle conditional classes', () => {
      const result = cn(
        'base-class',
        true && 'conditional-class',
        false && 'hidden-class'
      )
      expect(result).toContain('base-class')
      expect(result).toContain('conditional-class')
      expect(result).not.toContain('hidden-class')
    })
  })
})
