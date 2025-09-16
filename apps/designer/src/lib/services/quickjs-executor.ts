import type { QuickJSContext, QuickJSRuntime } from 'quickjs-emscripten'

export class QuickJSExecutor {
  private runtime?: QuickJSRuntime
  private context?: QuickJSContext
  private initialized = false
  private consoleLogs: string[] = []
  private shouldInterrupt = false
  private executionStartTime = 0

  async initialize() {
    if (this.initialized) return

    // Skip initialization during SSR (server-side rendering)
    if (typeof window === 'undefined') {
      console.warn('QuickJS not available during SSR - skipping initialization')
      return
    }

    try {
      // Dynamic import to avoid SSR issues
      const { getQuickJS } = await import('quickjs-emscripten')
      const QuickJS = await getQuickJS()

      this.runtime = QuickJS.newRuntime()

      // Set resource limits
      this.runtime.setMemoryLimit(1024 * 1024 * 10) // 10MB memory limit
      this.runtime.setMaxStackSize(1024 * 256) // 256KB stack limit

      // Set up interrupt handler for proper timeout
      this.runtime.setInterruptHandler(() => {
        // Return true to interrupt execution
        return this.shouldInterrupt
      })

      this.context = this.runtime.newContext()

      // Add console.log, console.error, console.warn support
      const createLogFunction = (prefix: string) => {
        return this.context.newFunction(prefix, (...args) => {
          const nativeArgs = args.map((arg) => this.context!.dump(arg))
          const message = nativeArgs
            .map((arg) =>
              typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
            )
            .join(' ')
          const logEntry =
            prefix === 'log' ? message : `[${prefix.toUpperCase()}] ${message}`
          this.consoleLogs.push(logEntry)
          // Forward to browser console
          if (prefix === 'log') {
            console.log(`[QuickJS]:`, message)
          } else if (prefix === 'error') {
            console.error(`[QuickJS]:`, message)
          } else if (prefix === 'warn') {
            console.warn(`[QuickJS]:`, message)
          }
        })
      }

      const consoleHandle = this.context.newObject()
      const logHandle = createLogFunction('log')
      const errorHandle = createLogFunction('error')
      const warnHandle = createLogFunction('warn')

      this.context.setProp(consoleHandle, 'log', logHandle)
      this.context.setProp(consoleHandle, 'error', errorHandle)
      this.context.setProp(consoleHandle, 'warn', warnHandle)
      this.context.setProp(this.context.global, 'console', consoleHandle)

      logHandle.dispose()
      errorHandle.dispose()
      warnHandle.dispose()
      consoleHandle.dispose()

      this.initialized = true

      console.log('QuickJS runtime initialized successfully')
    } catch (error) {
      throw new Error(
        `Failed to initialize QuickJS: ${(error as Error).message}`
      )
    }
  }

  async execute(
    code: string,
    inputs: Record<string, unknown>,
    timeout = 1000
  ): Promise<{ result: unknown; logs: string[] }> {
    // Clear previous logs and reset interrupt flag
    this.consoleLogs = []
    this.shouldInterrupt = false

    // Ensure initialization
    if (!this.initialized) {
      await this.initialize()
    }

    // If we're in SSR or initialization failed, throw a clear error
    if (!this.context) {
      throw new Error(
        'QuickJS execution not available (running in SSR or initialization failed)'
      )
    }

    try {
      // Create a clean execution environment
      const executionCode = this.buildExecutionCode(code, inputs)

      // Set up timeout interrupt
      this.executionStartTime = Date.now()
      const checkInterval = setInterval(() => {
        if (Date.now() - this.executionStartTime > timeout) {
          this.shouldInterrupt = true
          clearInterval(checkInterval)
        }
      }, 10) // Check every 10ms

      try {
        const result = await this.executeWithInterrupt(executionCode)
        clearInterval(checkInterval)

        return {
          result,
          logs: [...this.consoleLogs],
        }
      } finally {
        clearInterval(checkInterval)
        this.shouldInterrupt = false
      }
    } catch (error) {
      if (this.shouldInterrupt) {
        throw new Error(`Execution timed out after ${timeout}ms`)
      }
      throw new Error(`Execution failed: ${(error as Error).message}`)
    }
  }

  private buildExecutionCode(
    code: string,
    inputs: Record<string, unknown>
  ): string {
    // Prepare input values for function call
    const inputValues = Object.values(inputs)
      .map((value) => JSON.stringify(value))
      .join(', ')

    // Create a sandboxed environment
    return `
      // User's function code
      ${code}

      // Execute the function if it exists
      (function() {
        if (typeof execute === 'function') {
          return execute(${inputValues});
        } else {
          throw new Error('No execute function found');
        }
      })();
    `
  }

  private async executeWithInterrupt(code: string): Promise<unknown> {
    const result = this.context!.evalCode(code)

    if (result.error) {
      const errorValue = this.context!.dump(result.error)
      result.error.dispose()
      throw new Error(
        typeof errorValue === 'string' ? errorValue : JSON.stringify(errorValue)
      )
    } else {
      const value = this.context!.dump(result.value)
      result.value.dispose()
      return value
    }
  }

  dispose() {
    try {
      this.context?.dispose()
      this.runtime?.dispose()
      this.initialized = false
    } catch (error) {
      console.warn('Error disposing QuickJS resources:', error)
    }
  }
}

// Singleton instance for reuse
let globalExecutor: QuickJSExecutor | null = null

export async function getQuickJSExecutor(): Promise<QuickJSExecutor> {
  if (!globalExecutor) {
    globalExecutor = new QuickJSExecutor()

    // Only initialize if we're in a browser environment
    if (typeof window !== 'undefined') {
      await globalExecutor.initialize()
    }
  }
  return globalExecutor
}
