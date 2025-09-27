import mqttTopics from '../../shared/mqtt_topics/topics.json';

// TopicConfig interface matching Python TopicConfig
export interface TopicConfig {
  topic: string;
  qos: number;
  retain: boolean;
}

// Type for the structure of topics.json with replaced values
export type AllTopics = {
  command: {
    get_config: {
      request: TopicConfig;
      response: TopicConfig;
    };
    reboot: {
      request: TopicConfig;
      response: TopicConfig;
    };
    set_value_to_point: {
      request: TopicConfig;
      response: TopicConfig;
    };
    start_monitoring: {
      request: TopicConfig;
      response: TopicConfig;
    };
    stop_monitoring: {
      request: TopicConfig;
      response: TopicConfig;
    };
  };
  status: {
    heartbeat: TopicConfig;
  };
  data: {
    point: TopicConfig;
    point_bulk: TopicConfig;
  };
  alert_management: {
    acknowledge: TopicConfig;
    resolve: TopicConfig;
  };
};

// Strongly typed params for all possible placeholders in topics.json
export type TopicParams = {
  organization_id?: string;
  site_id?: string;
  iot_device_id?: string;
  iot_device_point_id?: string;
  tenant_id?: string;
};

export enum CommandNameEnum {
  GET_CONFIG = 'get_config',
  REBOOT = 'reboot',
  SET_VALUE_TO_POINT = 'set_value_to_point',
  START_MONITORING = 'start_monitoring',
  STOP_MONITORING = 'stop_monitoring',
}

function buildTopic(template: string, params: Record<string, string>) {
  return template.replace(/{(\w+)}/g, (_, key) => params[key]);
}

export const getAllTopics = ({ params }: { params: TopicParams }) => {
  function replaceInObject(obj: any): any {
    if (typeof obj === 'string') {
      const matches = obj.match(/{(\w+)}/g);
      if (!matches) return obj;
      for (const match of matches) {
        const key = match.slice(1, -1);
        if (!(key in params) || (params as Record<string, string>)[key] === undefined) return '';
      }
      return buildTopic(obj, params as Record<string, string>);
    } else if (typeof obj === 'object' && obj !== null) {
      const result: any = Array.isArray(obj) ? [] : {};
      for (const k in obj) {
        result[k] = replaceInObject(obj[k]);
      }
      return result;
    }
    return obj;
  }
  return replaceInObject(mqttTopics) as AllTopics;
};

function buildMQTTSubscriptionPattern(topicTemplate: string): string {
  return topicTemplate.replace(/\{[^}]+\}/g, '+');
}

export const getGlobalTopicsToWriteToDB = (): string[] => {
  // MQTT shared subscription with queue for load balancing across multiple instances
  // See: https://docs.emqx.com/en/emqx/latest/messaging/mqtt-shared-subscription.html
  // Using $queue pattern to ensure only one instance processes each message

  const topics = [
    buildMQTTSubscriptionPattern(mqttTopics.data.point_bulk.topic),
    buildMQTTSubscriptionPattern(mqttTopics.command.set_value_to_point.response.topic).replace('set_value_to_point', '+'),
    buildMQTTSubscriptionPattern(mqttTopics.status.heartbeat.topic),
    buildMQTTSubscriptionPattern(mqttTopics.alert_management.acknowledge.topic),
    buildMQTTSubscriptionPattern(mqttTopics.alert_management.resolve.topic)
  ];

  // Add queue prefix for load balancing across multiple instances
  return topics.map(topic => `$queue/${topic}`);
}
