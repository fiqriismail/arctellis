/**
 * Extract a Markdown table's header labels and body rows from the react-markdown
 * `node` (a hast Element). Kept separate from rendering so chart data does not
 * depend on the cell-rendering components. Pure and unit-tested.
 */

interface HastNode {
  type: string
  tagName?: string
  value?: string
  children?: HastNode[]
}

/** Concatenate all descendant text of a node. */
function nodeText(node: HastNode): string {
  if (node.type === 'text') return node.value ?? ''
  return (node.children ?? []).map(nodeText).join('')
}

function childElements(node: HastNode | undefined, tagName: string): HastNode[] {
  return (node?.children ?? []).filter(
    (c) => c.type === 'element' && c.tagName === tagName,
  )
}

function firstChild(node: HastNode | undefined, tagName: string): HastNode | undefined {
  return childElements(node, tagName)[0]
}

export interface ExtractedTable {
  headers: string[]
  rows: string[][]
}

export function extractTableFromNode(input: unknown): ExtractedTable {
  const node = input as HastNode
  if (!node || node.type !== 'element' || node.tagName !== 'table') {
    return { headers: [], rows: [] }
  }

  const thead = firstChild(node, 'thead')
  const headerRow = firstChild(thead, 'tr')
  const headers = childElements(headerRow, 'th').map(nodeText)

  const tbody = firstChild(node, 'tbody')
  const rows = childElements(tbody, 'tr').map((tr) =>
    childElements(tr, 'td').map(nodeText),
  )

  return { headers, rows }
}
