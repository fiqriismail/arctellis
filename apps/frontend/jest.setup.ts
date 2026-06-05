import '@testing-library/jest-dom'
import { TextEncoder, TextDecoder } from 'util'

// jsdom does not implement scrollIntoView — mock it globally
window.HTMLElement.prototype.scrollIntoView = jest.fn()

// jsdom does not expose TextEncoder/TextDecoder — provide Node's implementations
Object.assign(global, { TextEncoder, TextDecoder })
