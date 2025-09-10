import {
  BacnetConfig,
  BacnetObjectType,
  generateBACnetPointId,
} from '@/types/infrastructure'

interface MockPointData {
  objectType: BacnetObjectType
  objectId: number
  name: string
  value: number | boolean
  units?: string
  desc: string
  multistateConfig?: string // Reference to multistate configuration
}

// Define state text mappings for multistate objects
const MULTISTATE_CONFIGS: Record<
  string,
  { numberOfStates: number; stateText: string[] }
> = {
  fanSpeed: {
    numberOfStates: 4,
    stateText: ['Off', 'Low', 'Medium', 'High'],
  },
  operatingMode: {
    numberOfStates: 5,
    stateText: ['Off', 'Cool', 'Heat', 'Auto', 'Emergency Heat'],
  },
  damperPosition: {
    numberOfStates: 4,
    stateText: ['Closed', 'Minimum', 'Normal', 'Maximum'],
  },
  scheduleMode: {
    numberOfStates: 4,
    stateText: ['Unoccupied', 'Occupied', 'Standby', 'Not Used'],
  },
  alarmPriority: {
    numberOfStates: 5,
    stateText: ['Normal', 'Low', 'Medium', 'High', 'Critical'],
  },
  filterStatus: {
    numberOfStates: 4,
    stateText: ['Clean', 'Normal', 'Dirty', 'Replace'],
  },
  valvePosition: {
    numberOfStates: 4,
    stateText: ['Closed', 'Minimum', 'Modulating', 'Open'],
  },
  maintenanceMode: {
    numberOfStates: 4,
    stateText: ['Normal', 'Test', 'Service', 'Emergency'],
  },
}

export function generateMockBACnetPoints(
  supervisorId: string,
  controllerId: string
): BacnetConfig[] {
  const baseData: MockPointData[] = [
    // Analog Inputs (8 sensors)
    {
      objectType: 'analog-input',
      objectId: 1001,
      name: 'Zone Temperature',
      value: 72.5,
      units: '°F',
      desc: 'Room temperature sensor',
    },
    {
      objectType: 'analog-input',
      objectId: 1002,
      name: 'Zone Humidity',
      value: 45,
      units: '%',
      desc: 'Relative humidity sensor',
    },
    {
      objectType: 'analog-input',
      objectId: 1003,
      name: 'Supply Air Pressure',
      value: 1.2,
      units: 'inWC',
      desc: 'Duct static pressure',
    },
    {
      objectType: 'analog-input',
      objectId: 1004,
      name: 'Return Air Temperature',
      value: 70.2,
      units: '°F',
      desc: 'Return air sensor',
    },
    {
      objectType: 'analog-input',
      objectId: 1005,
      name: 'Outside Air Temperature',
      value: 85.3,
      units: '°F',
      desc: 'OAT sensor',
    },
    {
      objectType: 'analog-input',
      objectId: 1006,
      name: 'CO2 Level',
      value: 450,
      units: 'ppm',
      desc: 'Indoor air quality',
    },
    {
      objectType: 'analog-input',
      objectId: 1007,
      name: 'Supply Water Temperature',
      value: 44,
      units: '°F',
      desc: 'Chilled water supply',
    },
    {
      objectType: 'analog-input',
      objectId: 1008,
      name: 'Return Water Temperature',
      value: 54,
      units: '°F',
      desc: 'Chilled water return',
    },

    // Analog Outputs (5 actuators)
    {
      objectType: 'analog-output',
      objectId: 2001,
      name: 'Cooling Valve',
      value: 35,
      units: '%',
      desc: 'Chilled water valve position',
    },
    {
      objectType: 'analog-output',
      objectId: 2002,
      name: 'Supply Damper',
      value: 75,
      units: '%',
      desc: 'VAV damper position',
    },
    {
      objectType: 'analog-output',
      objectId: 2003,
      name: 'Return Fan Speed',
      value: 60,
      units: '%',
      desc: 'VFD speed command',
    },
    {
      objectType: 'analog-output',
      objectId: 2004,
      name: 'Heating Valve',
      value: 0,
      units: '%',
      desc: 'Hot water valve position',
    },
    {
      objectType: 'analog-output',
      objectId: 2005,
      name: 'OA Damper',
      value: 20,
      units: '%',
      desc: 'Outside air damper',
    },

    // Analog Values (6 setpoints)
    {
      objectType: 'analog-value',
      objectId: 3001,
      name: 'Zone Temp Setpoint',
      value: 72,
      units: '°F',
      desc: 'Occupied cooling setpoint',
    },
    {
      objectType: 'analog-value',
      objectId: 3002,
      name: 'Zone Humidity Setpoint',
      value: 50,
      units: '%',
      desc: 'Target humidity',
    },
    {
      objectType: 'analog-value',
      objectId: 3003,
      name: 'Duct Pressure Setpoint',
      value: 1.5,
      units: 'inWC',
      desc: 'Static pressure target',
    },
    {
      objectType: 'analog-value',
      objectId: 3004,
      name: 'Deadband',
      value: 2,
      units: '°F',
      desc: 'Temperature deadband',
    },
    {
      objectType: 'analog-value',
      objectId: 3005,
      name: 'Night Setback',
      value: 5,
      units: '°F',
      desc: 'Unoccupied setback',
    },
    {
      objectType: 'analog-value',
      objectId: 3006,
      name: 'CO2 Setpoint',
      value: 800,
      units: 'ppm',
      desc: 'Ventilation control',
    },

    // Binary Inputs (7 status)
    {
      objectType: 'binary-input',
      objectId: 4001,
      name: 'Occupancy Status',
      value: true,
      desc: 'Space occupied sensor',
    },
    {
      objectType: 'binary-input',
      objectId: 4002,
      name: 'Filter Alarm',
      value: false,
      desc: 'Dirty filter switch',
    },
    {
      objectType: 'binary-input',
      objectId: 4003,
      name: 'Smoke Detector',
      value: false,
      desc: 'Smoke alarm status',
    },
    {
      objectType: 'binary-input',
      objectId: 4004,
      name: 'Freeze Stat',
      value: false,
      desc: 'Freeze protection',
    },
    {
      objectType: 'binary-input',
      objectId: 4005,
      name: 'High Temp Alarm',
      value: false,
      desc: 'Over temperature',
    },
    {
      objectType: 'binary-input',
      objectId: 4006,
      name: 'Fan Status',
      value: true,
      desc: 'Fan running feedback',
    },
    {
      objectType: 'binary-input',
      objectId: 4007,
      name: 'Door Contact',
      value: false,
      desc: 'Equipment room door',
    },

    // Binary Outputs (6 commands)
    {
      objectType: 'binary-output',
      objectId: 5001,
      name: 'Supply Fan',
      value: true,
      desc: 'Fan start/stop command',
    },
    {
      objectType: 'binary-output',
      objectId: 5002,
      name: 'Return Fan',
      value: true,
      desc: 'Return fan command',
    },
    {
      objectType: 'binary-output',
      objectId: 5003,
      name: 'Cooling Enable',
      value: true,
      desc: 'Cooling mode enable',
    },
    {
      objectType: 'binary-output',
      objectId: 5004,
      name: 'Heating Enable',
      value: false,
      desc: 'Heating mode enable',
    },
    {
      objectType: 'binary-output',
      objectId: 5005,
      name: 'Alarm Light',
      value: false,
      desc: 'Visual alarm indicator',
    },
    {
      objectType: 'binary-output',
      objectId: 5006,
      name: 'UV Light',
      value: true,
      desc: 'UV sterilization',
    },

    // Binary Values (6 modes)
    {
      objectType: 'binary-value',
      objectId: 6001,
      name: 'System Enable',
      value: true,
      desc: 'Master system enable',
    },
    {
      objectType: 'binary-value',
      objectId: 6002,
      name: 'Maintenance Mode',
      value: false,
      desc: 'Service mode active',
    },
    {
      objectType: 'binary-value',
      objectId: 6003,
      name: 'Emergency Override',
      value: false,
      desc: 'Emergency shutdown',
    },
    {
      objectType: 'binary-value',
      objectId: 6004,
      name: 'Schedule Override',
      value: false,
      desc: 'Manual schedule override',
    },
    {
      objectType: 'binary-value',
      objectId: 6005,
      name: 'Economizer Enable',
      value: true,
      desc: 'Free cooling mode',
    },
    {
      objectType: 'binary-value',
      objectId: 6006,
      name: 'Night Purge',
      value: false,
      desc: 'Night flush enable',
    },

    // Multistate Inputs (3 sensors)
    {
      objectType: 'multistate-input',
      objectId: 7001,
      name: 'Fan Speed Status',
      value: 2,
      desc: 'Current fan speed',
      multistateConfig: 'fanSpeed',
    },
    {
      objectType: 'multistate-input',
      objectId: 7002,
      name: 'Operating Mode',
      value: 3,
      desc: 'Current HVAC mode',
      multistateConfig: 'operatingMode',
    },
    {
      objectType: 'multistate-input',
      objectId: 7003,
      name: 'Filter Status',
      value: 1,
      desc: 'Air filter condition',
      multistateConfig: 'filterStatus',
    },

    // Multistate Outputs (3 commands)
    {
      objectType: 'multistate-output',
      objectId: 8001,
      name: 'Fan Speed Command',
      value: 2,
      desc: 'Set fan speed',
      multistateConfig: 'fanSpeed',
    },
    {
      objectType: 'multistate-output',
      objectId: 8002,
      name: 'Damper Position',
      value: 2,
      desc: 'OA damper position',
      multistateConfig: 'damperPosition',
    },
    {
      objectType: 'multistate-output',
      objectId: 8003,
      name: 'Valve Position',
      value: 1,
      desc: 'Water valve control',
      multistateConfig: 'valvePosition',
    },

    // Multistate Values (3 virtual points)
    {
      objectType: 'multistate-value',
      objectId: 9001,
      name: 'Schedule Mode',
      value: 1,
      desc: 'Building schedule state',
      multistateConfig: 'scheduleMode',
    },
    {
      objectType: 'multistate-value',
      objectId: 9002,
      name: 'Alarm Priority',
      value: 0,
      desc: 'System alarm level',
      multistateConfig: 'alarmPriority',
    },
    {
      objectType: 'multistate-value',
      objectId: 9003,
      name: 'Maintenance Mode',
      value: 0,
      desc: 'System maintenance state',
      multistateConfig: 'maintenanceMode',
    },
  ]

  return baseData.map((item) => {
    const config: BacnetConfig = {
      pointId: generateBACnetPointId({
        supervisorId,
        controllerId,
        objectId: item.objectId,
      }), // Deterministic ID
      objectType: item.objectType,
      objectId: item.objectId,
      supervisorId,
      controllerId,
      discoveredProperties: {
        presentValue:
          typeof item.value === 'number'
            ? item.objectType.includes('multistate')
              ? item.value // Keep multistate values as-is (state numbers)
              : Math.round(
                  (item.value + (Math.random() - 0.5) * (item.value * 0.1)) * 10
                ) / 10
            : Math.random() > 0.5,
        units: item.units,
        description: item.desc,
        reliability: 'no-fault-detected',
        statusFlags: {
          inAlarm: false,
          fault: false,
          overridden: false,
          outOfService: false,
        },
        // Add multistate-specific properties
        ...(item.objectType.includes('multistate') && item.multistateConfig
          ? {
              numberOfStates:
                MULTISTATE_CONFIGS[item.multistateConfig].numberOfStates,
              stateText: MULTISTATE_CONFIGS[item.multistateConfig].stateText,
            }
          : {}),
        // Add some optional properties randomly for analog objects
        ...(Math.random() > 0.5 && item.objectType.includes('analog')
          ? {
              minPresValue: 0,
              maxPresValue: 100,
              resolution: 0.1,
            }
          : {}),
        ...(Math.random() > 0.7
          ? {
              covIncrement: 1,
            }
          : {}),
      },
      name: item.name,
      position: undefined,
    }
    return config
  })
}

export async function discoverBACnetPoints(
  supervisorId: string,
  controllerId: string
): Promise<BacnetConfig[]> {
  // Simulate network delay
  await new Promise((resolve) =>
    setTimeout(resolve, 1500 + Math.random() * 1500)
  )

  const allPoints = generateMockBACnetPoints(supervisorId, controllerId)

  // Return 60-100% of points randomly
  const percentage = 0.6 + Math.random() * 0.4
  const count = Math.floor(allPoints.length * percentage)

  // Shuffle and return subset
  const shuffled = [...allPoints].sort(() => Math.random() - 0.5)
  return shuffled.slice(0, count)
}
