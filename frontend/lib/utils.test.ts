import { cn } from './utils'

describe('cn utility function', () => {
  it('should combine class names correctly', () => {
    const result = cn('class1', 'class2')
    expect(result).toBe('class1 class2')
  })

  it('should merge tailwind classes correctly', () => {
    const result = cn('px-2 py-1', 'px-3')
    expect(result).toBe('py-1 px-3')
  })

  it('should handle conditional classes', () => {
    const result = cn('base-class', true && 'conditional-class', false && 'hidden-class')
    expect(result).toBe('base-class conditional-class')
  })

  it('should handle undefined and null values', () => {
    const result = cn('base-class', undefined, null, 'another-class')
    expect(result).toBe('base-class another-class')
  })

  it('should handle empty strings', () => {
    const result = cn('base-class', '', 'another-class')
    expect(result).toBe('base-class another-class')
  })

  it('should handle arrays of classes', () => {
    const result = cn(['class1', 'class2'], 'class3')
    expect(result).toBe('class1 class2 class3')
  })

  it('should handle object-based conditions', () => {
    const result = cn({
      'active': true,
      'disabled': false,
      'primary': true,
    })
    expect(result).toBe('active primary')
  })

  it('should handle complex combinations', () => {
    const isActive = true
    const isDisabled = false
    const size = 'lg'

    const result = cn(
      'btn',
      {
        'btn-active': isActive,
        'btn-disabled': isDisabled,
      },
      size === 'lg' && 'btn-lg',
      'text-white'
    )

    expect(result).toBe('btn btn-active btn-lg text-white')
  })
})
