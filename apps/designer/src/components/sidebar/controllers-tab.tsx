'use client'

import { ControllersTreeContainer } from '@/containers/controllers-tree-container'
import { PointPropertiesContainer } from '@/containers/point-properties-container'
import { useInfrastructureStore } from '@/store/use-infrastructure-store'

export function ControllersTab() {
  const selectedPointId = useInfrastructureStore(
    (state) => state.selectedPointId
  )

  return (
    <div className="h-full flex flex-col">
      {/* Tree view takes most of the space */}
      <div className="flex-1 min-h-0">
        <ControllersTreeContainer />
      </div>

      {/* Properties panel shows when a point is selected */}
      {selectedPointId && (
        <div className="h-1/3 border-t overflow-y-auto">
          <PointPropertiesContainer />
        </div>
      )}
    </div>
  )
}
