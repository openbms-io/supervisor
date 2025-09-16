import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

interface FunctionTimeoutConfigProps {
  timeout: number
  onTimeoutChange: (timeout: number) => void
}

export const FunctionTimeoutConfig = ({
  timeout,
  onTimeoutChange,
}: FunctionTimeoutConfigProps) => {
  return (
    <div className="space-y-2">
      <Label htmlFor="timeout">Execution Timeout</Label>
      <div className="flex items-center gap-2">
        <Input
          id="timeout"
          type="number"
          value={timeout}
          onChange={(e) => onTimeoutChange(Number(e.target.value))}
          min={100}
          max={10000}
          className="w-32"
        />
        <span className="text-sm text-muted-foreground">milliseconds</span>
      </div>
      <p className="text-xs text-muted-foreground">
        Maximum time allowed for function execution (100-10000ms)
      </p>
    </div>
  )
}
