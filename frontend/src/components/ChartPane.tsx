import React, { ReactNode } from 'react'

interface ChartPaneProps {
  title: string
  children: ReactNode
  actions?: ReactNode
}

export function ChartPane({ title, children, actions }: ChartPaneProps) {
  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h3 style={styles.title}>{title}</h3>
        {actions && <div style={styles.actions}>{actions}</div>}
      </div>
      <div style={styles.content}>{children}</div>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    backgroundColor: 'white',
    border: '1px solid #e0e0e0',
    padding: '16px',
    marginBottom: '20px',
    borderRadius: '4px',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '16px',
  },
  title: {
    margin: 0,
    fontSize: '18px',
    fontWeight: '600',
  },
  actions: {
    display: 'flex',
    gap: '8px',
  },
  content: {
    width: '100%',
  },
}
