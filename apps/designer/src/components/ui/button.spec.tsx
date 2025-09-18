import { render } from '@test-utils/render'
import { Button } from './button'

describe('Button Component', () => {
  it('should render button with text', () => {
    const { getByText } = render(<Button>Click me</Button>)
    expect(getByText('Click me')).toBeInTheDocument()
  })

  it('should apply variant classes correctly', () => {
    const { container } = render(<Button variant="destructive">Delete</Button>)
    const button = container.querySelector('button')
    expect(button).toHaveClass('bg-destructive')
  })

  it('should handle disabled state', () => {
    const { container } = render(<Button disabled>Disabled</Button>)
    const button = container.querySelector('button')
    expect(button).toBeDisabled()
  })
})
