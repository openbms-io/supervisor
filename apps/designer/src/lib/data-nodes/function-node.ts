import {
  LogicNode,
  ComputeValue,
  NodeCategory,
  NodeDirection,
  generateInstanceId,
  DataNode,
} from '@/types/infrastructure'
import { Message, SendCallback } from '@/lib/message-system/types'
import { getQuickJSExecutor } from '@/lib/services/quickjs-executor'
import { v4 as uuidv4 } from 'uuid'

export interface FunctionInput {
  id: string // 'input1', 'input2', etc.
  label: string // User-friendly display name
}

export interface FunctionNodeMetadata {
  code: string
  inputs: FunctionInput[]
  timeout?: number
}

export class FunctionNode implements LogicNode {
  readonly id: string
  readonly type = 'function' as const
  readonly category = NodeCategory.LOGIC
  readonly label: string
  readonly direction = NodeDirection.BIDIRECTIONAL

  private runtimeInitialized = false
  private _metadata: FunctionNodeMetadata
  private messageBuffer: Map<string, Message> = new Map()
  private sendCallback?: SendCallback<string>
  private _computedValue?: ComputeValue
  private _lastError?: string
  private _consoleLogs: string[] = []

  public stateDidChange?: (stateData: {
    result?: ComputeValue
    error?: string
    consoleLogs: string[]
  }) => void

  get metadata(): FunctionNodeMetadata {
    return this._metadata
  }

  get computedValue(): ComputeValue | undefined {
    return this._computedValue
  }

  get lastError(): string | undefined {
    return this._lastError
  }

  get consoleLogs(): string[] {
    return this._consoleLogs
  }

  constructor(label: string, metadata?: Partial<FunctionNodeMetadata>) {
    this.id = generateInstanceId()
    this.label = label
    this._metadata = {
      code: metadata?.code || 'function execute(input1) {\n  return input1;\n}',
      inputs: metadata?.inputs || [{ id: 'input1', label: 'Input 1' }],
      timeout: metadata?.timeout || 1000,
    }
  }

  async initializeRuntime() {
    if (!this.runtimeInitialized) {
      try {
        // Initialize QuickJS executor (singleton)
        await getQuickJSExecutor()
        this.runtimeInitialized = true
      } catch (error) {
        this._lastError = `Failed to initialize runtime: ${
          (error as Error).message
        }`
        console.error(`[${this.id}] Runtime initialization failed:`, error)
        this.stateDidChange?.({
          error: this._lastError,
          consoleLogs: this._consoleLogs,
        })
      }
    }
  }

  // Dynamic input management
  addInput(label?: string): void {
    const nextId = `input${this._metadata.inputs.length + 1}`
    this._metadata.inputs.push({
      id: nextId,
      label: label || `Input ${this._metadata.inputs.length + 1}`,
    })
  }

  removeInput(id: string): void {
    this._metadata.inputs = this._metadata.inputs.filter((i) => i.id !== id)
    this.messageBuffer.delete(id) // Clean up buffer
  }

  updateCode(code: string): void {
    this._metadata.code = code
    this._lastError = undefined
    this.stateDidChange?.({
      error: undefined,
      consoleLogs: this._consoleLogs,
    })
  }

  // Public methods for proper encapsulation
  setInputs(inputs: FunctionInput[]): void {
    this._metadata.inputs = inputs
  }

  setTimeout(timeout: number): void {
    this._metadata.timeout = timeout
  }

  updateConfig(config: {
    code?: string
    inputs?: FunctionInput[]
    timeout?: number
  }): void {
    if (config.code !== undefined) {
      this._metadata.code = config.code
    }
    if (config.inputs !== undefined) {
      this._metadata.inputs = config.inputs
    }
    if (config.timeout !== undefined) {
      this._metadata.timeout = config.timeout
    }
    // Clear error when config updates
    this._lastError = undefined
    this.stateDidChange?.({
      error: undefined,
      consoleLogs: this._consoleLogs,
    })
  }

  // LogicNode interface implementation
  getValue(): ComputeValue | undefined {
    return this._computedValue
  }

  getInputValues(): ComputeValue[] {
    return this._metadata.inputs
      .map((input) => this.messageBuffer.get(input.id)?.payload)
      .filter((v) => v !== undefined) as ComputeValue[]
  }

  reset(): void {
    this._computedValue = undefined
    this._lastError = undefined
    this.messageBuffer.clear()
    this.stateDidChange?.({
      result: undefined,
      error: undefined,
      consoleLogs: this._consoleLogs,
    })
  }

  canConnectWith(target: DataNode): boolean {
    return target.direction !== NodeDirection.OUTPUT
  }

  getInputHandles(): readonly string[] {
    return this._metadata.inputs.map((i) => i.id)
  }

  getOutputHandles(): readonly string[] {
    return ['output']
  }

  // Message passing implementation
  setSendCallback(callback: SendCallback<string>): void {
    this.sendCallback = callback
  }

  private async send(message: Message, handle: string): Promise<void> {
    if (this.sendCallback) {
      await this.sendCallback(message, this.id, handle)
    }
  }

  async receive(
    message: Message,
    handle: string,
    fromNodeId: string
  ): Promise<void> {
    console.log(
      `🔧 [${this.id}] Function received on ${handle}:`,
      message.payload,
      `from ${fromNodeId}`
    )

    // Initialize runtime if needed
    await this.initializeRuntime()

    // Buffer the message
    this.messageBuffer.set(handle, message)

    // Check if all inputs received
    const hasAllInputs = this._metadata.inputs.every((input) =>
      this.messageBuffer.has(input.id)
    )

    if (hasAllInputs) {
      console.log(`✅ [${this.id}] All inputs received, executing function...`)

      // Prepare input values object
      const inputValues: Record<string, unknown> = {}
      this._metadata.inputs.forEach((input) => {
        inputValues[input.id] = this.messageBuffer.get(input.id)?.payload
      })

      try {
        // Execute user function
        const result = await this.executeFunction(inputValues)
        this._computedValue = result
        this._lastError = undefined

        console.log(`🔧 [${this.id}] Function executed:`, result)

        // Notify UI of successful execution
        this.stateDidChange?.({
          result,
          error: undefined,
          consoleLogs: this._consoleLogs,
        })

        // Send result
        await this.send(
          {
            payload: result,
            _msgid: uuidv4(),
            timestamp: Date.now(),
            metadata: { source: this.id, type: 'function' },
          },
          'output'
        )
      } catch (error) {
        this._lastError = (error as Error).message
        console.error(`❌ [${this.id}] Function error:`, error)

        // Notify UI of error
        this.stateDidChange?.({
          result: this._computedValue,
          error: this._lastError,
          consoleLogs: this._consoleLogs,
        })

        // Send undefined on error
        await this.send(
          {
            payload: undefined,
            _msgid: uuidv4(),
            timestamp: Date.now(),
            metadata: { source: this.id, error: (error as Error).message },
          },
          'output'
        )
      }

      // Clear buffer for next execution
      this.messageBuffer.clear()
    } else {
      console.log(`⏳ [${this.id}] Waiting for more inputs...`)
    }
  }

  private async executeFunction(
    inputs: Record<string, unknown>
  ): Promise<ComputeValue> {
    try {
      // Get the QuickJS executor
      const executor = await getQuickJSExecutor()

      // Execute the user code with QuickJS - now returns object with result and logs
      const { result, logs } = await executor.execute(
        this._metadata.code,
        inputs,
        this._metadata.timeout || 1000
      )

      // Store console logs
      this._consoleLogs = logs

      // Validate return type
      if (typeof result !== 'number' && typeof result !== 'boolean') {
        throw new Error(
          `Function must return number or boolean, got ${typeof result}`
        )
      }

      return result as ComputeValue
    } catch (error) {
      throw new Error(
        `Function execution failed: ${
          error instanceof Error ? error.message : String(error)
        }`
      )
    }
  }
}
