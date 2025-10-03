import { getAllTopics, getGlobalTopicsToWriteToDB, TopicParams, AllTopics, TopicConfig } from './topics_loader.js';

describe('topics_loader', () => {
  describe('getAllTopics', () => {
    it('should return AllTopics with placeholder replacement for complete parameters', () => {
      const params: TopicParams = {
        organization_id: 'test-org',
        site_id: 'test-site',
        iot_device_id: 'test-iot-device',
        controller_device_id: 'test-controller',
        iot_device_point_id: 'test-point',
      };

      const result = getAllTopics({ params });

      expect(result).toBeDefined();
      expect(result.command.get_config.request.topic).toBe(
        'iot/global/test-org/test-site/test-iot-device/command/get_config/request'
      );
      expect(result.command.get_config.response.topic).toBe(
        'iot/global/test-org/test-site/test-iot-device/command/get_config/response'
      );
      expect(result.command.reboot.request.topic).toBe(
        'iot/global/test-org/test-site/test-iot-device/command/reboot/request'
      );
      expect(result.status.heartbeat.topic).toBe(
        'iot/global/test-org/test-site/test-iot-device/status/heartbeat'
      );
      expect(result.data.point?.topic).toBe(
        'iot/global/test-org/test-site/test-iot-device/test-controller/test-point'
      );
      expect(result.data.point_bulk.topic).toBe(
        'iot/global/test-org/test-site/test-iot-device/bulk'
      );
    });

    it('should return AllTopics with TopicConfig objects having correct properties', () => {
      const params: TopicParams = {
        organization_id: 'test-org',
        site_id: 'test-site',
        iot_device_id: 'test-iot-device',
        controller_device_id: 'test-controller',
        iot_device_point_id: 'test-point',
      };

      const result = getAllTopics({ params });

      // Test TopicConfig structure
      const commandConfig = result.command.get_config.request;
      expect(commandConfig).toHaveProperty('topic');
      expect(commandConfig).toHaveProperty('qos');
      expect(commandConfig).toHaveProperty('retain');
      expect(typeof commandConfig.topic).toBe('string');
      expect(typeof commandConfig.qos).toBe('number');
      expect(typeof commandConfig.retain).toBe('boolean');

      // Test QoS values
      expect(result.command.get_config.request.qos).toBe(1);
      expect(result.command.get_config.response.qos).toBe(1);
      expect(result.status.heartbeat.qos).toBe(1);
      expect(result.data.point?.qos).toBe(1);
      expect(result.data.point_bulk.qos).toBe(0);

      // Test retain values
      expect(result.command.get_config.request.retain).toBe(false);
      expect(result.status.heartbeat.retain).toBe(true);
      expect(result.data.point?.retain).toBe(true);
      expect(result.data.point_bulk.retain).toBe(false);
    });

    it('should set data.point to null when controller_device_id is missing', () => {
      const params: TopicParams = {
        organization_id: 'test-org',
        site_id: 'test-site',
        iot_device_id: 'test-iot-device',
        iot_device_point_id: 'test-point',
      };

      const result = getAllTopics({ params });

      expect(result.data.point).toBeNull();
      expect(result.data.point_bulk.topic).toBe(
        'iot/global/test-org/test-site/test-iot-device/bulk'
      );
    });

    it('should set data.point to null when iot_device_point_id is missing', () => {
      const params: TopicParams = {
        organization_id: 'test-org',
        site_id: 'test-site',
        iot_device_id: 'test-iot-device',
        controller_device_id: 'test-controller',
      };

      const result = getAllTopics({ params });

      expect(result.data.point).toBeNull();
      expect(result.data.point_bulk.topic).toBe(
        'iot/global/test-org/test-site/test-iot-device/bulk'
      );
    });

    it('should set data.point to null when both controller_device_id and iot_device_point_id are missing', () => {
      const params: TopicParams = {
        organization_id: 'test-org',
        site_id: 'test-site',
        iot_device_id: 'test-iot-device',
      };

      const result = getAllTopics({ params });

      expect(result.data.point).toBeNull();
      expect(result.data.point_bulk.topic).toBe(
        'iot/global/test-org/test-site/test-iot-device/bulk'
      );
    });

    it('should leave placeholders unreplaced when parameter values are undefined', () => {
      const params: TopicParams = {
        organization_id: 'test-org',
        site_id: 'test-site',
      };

      const result = getAllTopics({ params });

      expect(result.command.get_config.request.topic).toContain('{iot_device_id}');
      expect(result.status.heartbeat.topic).toContain('{iot_device_id}');
    });

    it('should handle empty parameters object', () => {
      const params: TopicParams = {};

      const result = getAllTopics({ params });

      expect(result).toBeDefined();
      expect(result.command.get_config.request.topic).toContain('{organization_id}');
      expect(result.command.get_config.request.topic).toContain('{site_id}');
      expect(result.command.get_config.request.topic).toContain('{iot_device_id}');
      expect(result.data.point).toBeNull();
    });

    it('should include all command types', () => {
      const params: TopicParams = {
        organization_id: 'test-org',
        site_id: 'test-site',
        iot_device_id: 'test-iot-device',
      };

      const result = getAllTopics({ params });

      expect(result.command).toHaveProperty('get_config');
      expect(result.command).toHaveProperty('reboot');
      expect(result.command).toHaveProperty('set_value_to_point');
      expect(result.command).toHaveProperty('start_monitoring');
      expect(result.command).toHaveProperty('stop_monitoring');

      // Test that all commands have request and response
      Object.values(result.command).forEach((command) => {
        expect(command).toHaveProperty('request');
        expect(command).toHaveProperty('response');
        expect(command.request).toHaveProperty('topic');
        expect(command.request).toHaveProperty('qos');
        expect(command.request).toHaveProperty('retain');
        expect(command.response).toHaveProperty('topic');
        expect(command.response).toHaveProperty('qos');
        expect(command.response).toHaveProperty('retain');
      });
    });

    it('should include alert_management section', () => {
      const params: TopicParams = {
        organization_id: 'test-org',
        site_id: 'test-site',
      };

      const result = getAllTopics({ params });

      expect(result.alert_management).toHaveProperty('acknowledge');
      expect(result.alert_management).toHaveProperty('resolve');
      expect(result.alert_management.acknowledge.topic).toBe(
        'iot/global/test-org/test-site/alert-management/acknowledge'
      );
      expect(result.alert_management.resolve.topic).toBe(
        'iot/global/test-org/test-site/alert-management/resolve'
      );
    });
  });

  describe('getGlobalTopicsToWriteToDB', () => {
    it('should return array of topics with queue prefix', () => {
      const topics = getGlobalTopicsToWriteToDB();

      expect(Array.isArray(topics)).toBe(true);
      expect(topics.length).toBeGreaterThan(0);

      // All topics should have $queue/ prefix
      topics.forEach((topic) => {
        expect(topic).toMatch(/^\$queue\//);
      });
    });

    it('should include expected topic patterns with wildcards', () => {
      const topics = getGlobalTopicsToWriteToDB();

      // Convert to strings without queue prefix for easier testing
      const topicPatterns = topics.map((topic) => topic.replace('$queue/', ''));

      // Should include bulk data topic pattern
      expect(topicPatterns.some((topic) =>
        topic.includes('iot/global/+/+/+/bulk')
      )).toBe(true);

      // Should include heartbeat pattern
      expect(topicPatterns.some((topic) =>
        topic.includes('iot/global/+/+/+/status/heartbeat')
      )).toBe(true);

      // Should include command response pattern
      expect(topicPatterns.some((topic) =>
        topic.includes('iot/global/+/+/+/command/+/response')
      )).toBe(true);

      // Should include alert management patterns
      expect(topicPatterns.some((topic) =>
        topic.includes('iot/global/+/+/alert-management/acknowledge')
      )).toBe(true);
      expect(topicPatterns.some((topic) =>
        topic.includes('iot/global/+/+/alert-management/resolve')
      )).toBe(true);
    });

    it('should return consistent topic list', () => {
      const topics1 = getGlobalTopicsToWriteToDB();
      const topics2 = getGlobalTopicsToWriteToDB();

      expect(topics1).toEqual(topics2);
    });

    it('should use + wildcards for placeholder replacement', () => {
      const topics = getGlobalTopicsToWriteToDB();

      topics.forEach((topic) => {
        // Should not contain any unreplaced placeholders
        expect(topic).not.toMatch(/\{[^}]+\}/);
        // Should contain + wildcards
        expect(topic).toMatch(/\+/);
      });
    });
  });

  describe('TypeScript types', () => {
    it('should have correct AllTopics type structure', () => {
      const params: TopicParams = {
        organization_id: 'test-org',
        site_id: 'test-site',
        iot_device_id: 'test-iot-device',
        controller_device_id: 'test-controller',
        iot_device_point_id: 'test-point',
      };

      const result: AllTopics = getAllTopics({ params });

      // TypeScript compilation will catch type errors
      // These tests verify runtime behavior matches type expectations
      expect(typeof result.command.get_config.request.topic).toBe('string');
      expect(typeof result.command.get_config.request.qos).toBe('number');
      expect(typeof result.command.get_config.request.retain).toBe('boolean');

      // data.point can be null or TopicConfig
      if (result.data.point) {
        expect(typeof result.data.point.topic).toBe('string');
        expect(typeof result.data.point.qos).toBe('number');
        expect(typeof result.data.point.retain).toBe('boolean');
      }
    });

    it('should accept optional TopicParams', () => {
      // These should all compile and run without errors
      getAllTopics({ params: {} });
      getAllTopics({ params: { organization_id: 'test' } });
      getAllTopics({ params: { organization_id: 'test', site_id: 'test' } });
      getAllTopics({
        params: {
          organization_id: 'test',
          site_id: 'test',
          iot_device_id: 'test',
          controller_device_id: 'test',
          iot_device_point_id: 'test',
          tenant_id: 'test'
        }
      });
    });
  });
});
