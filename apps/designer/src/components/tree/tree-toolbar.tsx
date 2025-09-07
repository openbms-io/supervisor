'use client'

import { Button } from '@/components/ui/button'
import {
  ChevronDown,
  ChevronRight,
  RefreshCw,
  Plus,
  Search,
} from 'lucide-react'
import { Input } from '@/components/ui/input'

interface TreeToolbarProps {
  onExpandAll: () => void
  onCollapseAll: () => void
  onRefresh?: () => void
  onAdd?: () => void
  searchValue?: string
  onSearchChange?: (value: string) => void
  showSearch?: boolean
  showAdd?: boolean
  showRefresh?: boolean
}

export function TreeToolbar({
  onExpandAll,
  onCollapseAll,
  onRefresh,
  onAdd,
  searchValue,
  onSearchChange,
  showSearch = false,
  showAdd = false,
  showRefresh = false,
}: TreeToolbarProps) {
  return (
    <div className="flex items-center gap-2 p-2 border-b">
      <div className="flex items-center gap-1">
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7"
          onClick={onExpandAll}
          title="Expand all"
        >
          <ChevronDown className="h-4 w-4" />
        </Button>

        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7"
          onClick={onCollapseAll}
          title="Collapse all"
        >
          <ChevronRight className="h-4 w-4" />
        </Button>

        {showRefresh && onRefresh && (
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={onRefresh}
            title="Refresh"
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
        )}

        {showAdd && onAdd && (
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={onAdd}
            title="Add new"
          >
            <Plus className="h-4 w-4" />
          </Button>
        )}
      </div>

      {showSearch && onSearchChange && (
        <div className="flex-1 relative">
          <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Search..."
            className="h-7 pl-7 text-xs"
            value={searchValue || ''}
            onChange={(e) => onSearchChange(e.target.value)}
          />
        </div>
      )}
    </div>
  )
}
