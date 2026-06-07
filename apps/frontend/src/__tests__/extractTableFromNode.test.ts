import { extractTableFromNode } from '@/features/chat/lib/extractTableFromNode'

// Minimal hast-like builders mirroring what react-markdown passes as `node`.
const text = (value: string) => ({ type: 'text', value })
const el = (tagName: string, children: unknown[]) => ({
  type: 'element',
  tagName,
  children,
})
const cell = (tag: string, value: string) => el(tag, [text(value)])

const tableNode = el('table', [
  el('thead', [el('tr', [cell('th', 'Status'), cell('th', 'Total')])]),
  el('tbody', [
    el('tr', [cell('td', 'Approved'), cell('td', '5000')]),
    el('tr', [cell('td', 'Rejected'), cell('td', '1200')]),
  ]),
])

describe('extractTableFromNode', () => {
  it('extracts headers from the thead row', () => {
    const { headers } = extractTableFromNode(tableNode)
    expect(headers).toEqual(['Status', 'Total'])
  })

  it('extracts body rows as arrays of cell text', () => {
    const { rows } = extractTableFromNode(tableNode)
    expect(rows).toEqual([
      ['Approved', '5000'],
      ['Rejected', '1200'],
    ])
  })

  it('concatenates nested inline text within a cell', () => {
    const node = el('table', [
      el('thead', [el('tr', [cell('th', 'Name')])]),
      el('tbody', [
        el('tr', [el('td', [text('RTP-'), el('strong', [text('143')])])]),
      ]),
    ])
    expect(extractTableFromNode(node).rows).toEqual([['RTP-143']])
  })

  it('returns empty structure for a non-table node', () => {
    expect(extractTableFromNode(el('p', [text('hi')]))).toEqual({
      headers: [],
      rows: [],
    })
  })
})
