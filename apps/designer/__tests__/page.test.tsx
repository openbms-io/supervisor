import { render, screen } from '@testing-library/react'
import Page from '@/app/page'

describe('Home Page', () => {
  it('renders successfully', () => {
    render(<Page />)
    // Just verify the page renders without errors
    expect(document.body).toBeInTheDocument()
  })
})
