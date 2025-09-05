'use client'

import React, { useState } from 'react'
import { SearchAndFilterProps, ProjectSort, ProjectOrder } from './types'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Search, SortAsc, SortDesc, Filter } from 'lucide-react'

export function SearchAndFilter({
  onSearch,
  onSort,
  searchQuery,
  currentSort,
  currentOrder,
}: SearchAndFilterProps): React.JSX.Element {
  const [localSearchQuery, setLocalSearchQuery] = useState<string>(searchQuery)

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    const value = e.target.value
    setLocalSearchQuery(value)
    onSearch({ query: value })
  }

  const handleSortChange = ({
    sort,
    order,
  }: {
    sort: ProjectSort
    order: ProjectOrder
  }): void => {
    onSort({ sort, order })
  }

  const getSortLabel = ({ sort }: { sort: ProjectSort }): string => {
    const labels: Record<ProjectSort, string> = {
      name: 'Name',
      created_at: 'Created Date',
      updated_at: 'Updated Date',
    }
    return labels[sort]
  }

  const getOrderIcon = ({
    order,
  }: {
    order: ProjectOrder
  }): React.JSX.Element => {
    return order === 'asc' ? (
      <SortAsc className="h-4 w-4" />
    ) : (
      <SortDesc className="h-4 w-4" />
    )
  }

  const sortOptions: Array<{ sort: ProjectSort; label: string }> = [
    { sort: 'name', label: 'Name' },
    { sort: 'updated_at', label: 'Updated Date' },
    { sort: 'created_at', label: 'Created Date' },
  ]

  return (
    <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
      <div className="relative flex-1 max-w-sm">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          type="text"
          placeholder="Search projects..."
          value={localSearchQuery}
          onChange={handleSearchChange}
          className="pl-9"
        />
      </div>

      <div className="flex items-center gap-2">
        <span className="text-sm font-medium text-muted-foreground">
          Sort by:
        </span>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm" className="h-9">
              <Filter className="h-4 w-4 mr-2" />
              {getSortLabel({ sort: currentSort })}
              {getOrderIcon({ order: currentOrder })}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-40">
            {sortOptions.map(({ sort, label }) => (
              <div key={sort}>
                <DropdownMenuItem
                  onClick={() => handleSortChange({ sort, order: 'asc' })}
                  className="flex items-center justify-between"
                >
                  <span>{label}</span>
                  <SortAsc className="h-4 w-4" />
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => handleSortChange({ sort, order: 'desc' })}
                  className="flex items-center justify-between"
                >
                  <span>{label}</span>
                  <SortDesc className="h-4 w-4" />
                </DropdownMenuItem>
              </div>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  )
}
