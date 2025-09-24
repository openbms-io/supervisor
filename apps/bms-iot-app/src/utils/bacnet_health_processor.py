from typing import List, Optional, Union, Dict
import logging

logger = logging.getLogger(__name__)


class BACnetHealthProcessor:
    """
    Utility class for processing BACnet health properties into SQLite-compatible formats.
    Converts raw BACnet property values into semicolon-separated strings for local storage.
    """

    @staticmethod
    def process_status_flags(raw_flags) -> Optional[str]:
        """
        Convert BACnet statusFlags to semicolon-separated string.
        Adds a check to see if the statusFlags is a string and if it is, it will return the string as-is.
        If not, it will convert the statusFlags array [1,0,1,0] to a semicolon-separated string.

        Args:
            raw_flags: BACnet StatusFlags object, array of 4 integers, or None
                      [in-alarm, fault, overridden, out-of-service]

        Returns:
            Semicolon-separated string of active flags (e.g., "fault;overridden")
            None if no flags are active or input is invalid

        Example:
            Input: [0, 1, 0, 1]  # fault and out-of-service flags set
            Output: "fault;out-of-service"
        """
        if raw_flags is None:
            return None

        try:
            # Handle BACnet StatusFlags object - convert to string and parse
            if hasattr(raw_flags, "__class__") and "StatusFlags" in str(
                raw_flags.__class__
            ):
                # Convert StatusFlags object to string representation
                status_str = str(raw_flags).strip()
                logger.debug(f"StatusFlags string representation: {status_str}")

                # Parse common StatusFlags string patterns
                # Examples: "" (no flags), "fault;overridden", "in-alarm;out-of-service"
                if not status_str or status_str == "":
                    return None

                # If the string already contains semicolons, return as-is
                if ";" in status_str:
                    return status_str

                # If single flag, return it
                if status_str in ["in-alarm", "fault", "overridden", "out-of-service"]:
                    return status_str

                # For other string formats, try to parse as space-separated or return as-is
                return status_str

            # Handle list of integers (original format)
            if isinstance(raw_flags, list) and len(raw_flags) == 4:
                flag_names = ["in-alarm", "fault", "overridden", "out-of-service"]
                active_flags = [
                    flag_names[i] for i, flag in enumerate(raw_flags) if flag == 1
                ]

                return ";".join(active_flags) if active_flags else None
            else:
                logger.debug(
                    f"Invalid statusFlags format: {raw_flags} (type: {type(raw_flags)})"
                )
                return None

        except Exception as e:
            logger.warning(f"Failed to process statusFlags {raw_flags}: {e}")
            return None

    @staticmethod
    def process_reliability(raw_reliability: Optional[str]) -> Optional[str]:
        """
        Pass through BACnet reliability string without validation.

        Args:
            raw_reliability: String reliability from BACnet

        Returns:
            Raw reliability string or None if empty/invalid type

        Example:
            Input: "no-fault-detected"
            Output: "no-fault-detected"
        """
        if not raw_reliability or not isinstance(raw_reliability, str):
            return None

        # Return any non-empty string as-is
        return raw_reliability.strip() if raw_reliability.strip() else None

    @staticmethod
    def process_out_of_service(raw_value: Optional[bool]) -> Optional[bool]:
        """
        Validate and pass through BACnet out-of-service flag.

        Args:
            raw_value: Boolean out-of-service flag from BACnet (already converted from BACnet objects)

        Returns:
            Boolean value or None if invalid

        Example:
            Input: True
            Output: True
        """
        if raw_value is None:
            return None

        if isinstance(raw_value, bool):
            return raw_value
        else:
            logger.warning(
                f"Invalid out-of-service value: {raw_value} (type: {type(raw_value)})"
            )
            return None

    @staticmethod
    def process_all_health_properties(raw_properties: dict) -> dict:
        """
        Process all health properties from a BACnet response.

        Args:
            raw_properties: Dictionary containing raw BACnet properties

        Returns:
            Dictionary with processed health properties

        Example:
            Input: {
                'statusFlags': [0, 1, 0, 0],
                'eventState': 'fault',
                'outOfService': False,
                'reliability': 'noFaultDetected'
            }
            Output: {
                'status_flags': 'fault',
                'event_state': 'fault',
                'out_of_service': False,
                'reliability': 'noFaultDetected'
            }
        """
        return {
            "status_flags": BACnetHealthProcessor.process_status_flags(
                raw_properties.get("statusFlags")
            ),
            "event_state": raw_properties.get("eventState"),
            "out_of_service": BACnetHealthProcessor.process_out_of_service(
                raw_properties.get("outOfService")
            ),
            "reliability": BACnetHealthProcessor.process_reliability(
                raw_properties.get("reliability")
            ),
        }

    # ===== TDD STUB METHODS - OPTIONAL PROPERTIES =====
    # These methods are stubs that will be implemented during TDD GREEN phase

    @staticmethod
    def process_priority_array(raw_priority_array) -> Optional[str]:
        """
        Convert BACnet PriorityArray to JSON string.

        Args:
            raw_priority_array: BACnet PriorityArray object or list of 16 values

        Returns:
            JSON string of array with nulls and values preserved

        Example:
            Input: PriorityArray([None, None, 22.5, None, ...])
            Output: "[null,null,22.5,null,null,null,null,null,50.0,null,null,null,null,null,null,20.0]"
        """
        if raw_priority_array is None:
            return None

        try:
            import json

            # Handle BACnet PriorityArray object
            if hasattr(raw_priority_array, "__class__") and (
                "PriorityArray" in str(raw_priority_array.__class__)
                or getattr(raw_priority_array.__class__, "__name__", "")
                == "PriorityArray"
            ):
                # Convert to list, preserving None values
                array_list = []
                for i in range(16):
                    try:
                        value = raw_priority_array[i]
                        array_list.append(None if value is None else float(value))
                    except Exception:
                        array_list.append(None)
                return json.dumps(array_list)

            # Handle list input
            elif isinstance(raw_priority_array, list) and len(raw_priority_array) == 16:
                return json.dumps(
                    [None if v is None else float(v) for v in raw_priority_array]
                )

            return None
        except Exception as e:
            logger.warning(f"Failed to process PriorityArray: {e}")
            return None

    @staticmethod
    def process_limit_enable(raw_limit_enable) -> Optional[str]:
        """
        Convert BACnet LimitEnable BitString to JSON.

        Args:
            raw_limit_enable: BACnet LimitEnable object (2-bit BitString)

        Returns:
            JSON string with lowLimitEnable and highLimitEnable flags

        Example:
            Input: LimitEnable([1, 1])  # Both limits enabled
            Output: '{"lowLimitEnable":true,"highLimitEnable":true}'
        """
        if raw_limit_enable is None:
            return None

        try:
            import json

            # Handle BACnet LimitEnable object
            if hasattr(raw_limit_enable, "__class__") and (
                "LimitEnable" in str(raw_limit_enable.__class__)
                or getattr(raw_limit_enable.__class__, "__name__", "") == "LimitEnable"
            ):
                # Parse the string representation or bit array
                limit_dict = {"lowLimitEnable": False, "highLimitEnable": False}

                # Try to extract bit values
                if hasattr(raw_limit_enable, "value"):
                    bits = raw_limit_enable.value
                    if len(bits) >= 2:
                        limit_dict["lowLimitEnable"] = bool(bits[0])
                        limit_dict["highLimitEnable"] = bool(bits[1])

                return json.dumps(limit_dict)

            # Handle list/array input [lowLimit, highLimit]
            elif (
                isinstance(raw_limit_enable, (list, tuple))
                and len(raw_limit_enable) >= 2
            ):
                return json.dumps(
                    {
                        "lowLimitEnable": bool(raw_limit_enable[0]),
                        "highLimitEnable": bool(raw_limit_enable[1]),
                    }
                )

            return None
        except Exception as e:
            logger.warning(f"Failed to process LimitEnable: {e}")
            return None

    @staticmethod
    def process_event_transition_bits(
        raw_bits, field_name="eventEnable"
    ) -> Optional[str]:
        """
        Convert BACnet EventTransitionBits to JSON.

        Args:
            raw_bits: BACnet EventTransitionBits object (3-bit BitString)
            field_name: Name of the field (eventEnable or ackedTransitions)

        Returns:
            JSON string with toFault, toNormal, toOffnormal flags

        Example:
            Input: EventTransitionBits([1, 1, 1])
            Output: '{"toFault":true,"toNormal":true,"toOffnormal":true}'
        """
        if raw_bits is None:
            return None

        try:
            import json

            # Handle BACnet EventTransitionBits object
            if hasattr(raw_bits, "__class__") and (
                "EventTransitionBits" in str(raw_bits.__class__)
                or getattr(raw_bits.__class__, "__name__", "") == "EventTransitionBits"
            ):
                transition_dict = {
                    "toFault": False,
                    "toNormal": False,
                    "toOffnormal": False,
                }

                # Extract bit values
                if hasattr(raw_bits, "value"):
                    bits = raw_bits.value
                    if len(bits) >= 3:
                        transition_dict["toFault"] = bool(bits[0])
                        transition_dict["toNormal"] = bool(bits[1])
                        transition_dict["toOffnormal"] = bool(bits[2])

                return json.dumps(transition_dict)

            # Handle list input [toFault, toNormal, toOffnormal]
            elif isinstance(raw_bits, (list, tuple)) and len(raw_bits) >= 3:
                return json.dumps(
                    {
                        "toFault": bool(raw_bits[0]),
                        "toNormal": bool(raw_bits[1]),
                        "toOffnormal": bool(raw_bits[2]),
                    }
                )

            return None
        except Exception as e:
            logger.warning(f"Failed to process {field_name}: {e}")
            return None

    @staticmethod
    def process_event_timestamps(raw_timestamps) -> Optional[str]:
        """
        Convert BACnet EventTimeStamps array to JSON.

        Args:
            raw_timestamps: Array of 3 TimeStamp objects

        Returns:
            JSON array of ISO 8601 timestamp strings or nulls

        Example:
            Input: [TimeStamp(2024-01-01 10:00:00), None, None]
            Output: '["2024-01-01T10:00:00Z",null,null]'
        """
        if raw_timestamps is None:
            return None

        try:
            import json

            timestamps: List[Optional[str]] = []

            # Process array of timestamps
            if hasattr(raw_timestamps, "__iter__"):
                for ts in raw_timestamps[:3]:  # Ensure max 3 elements
                    if ts is None:
                        timestamps.append(None)
                    elif hasattr(ts, "isoformat"):
                        timestamps.append(ts.isoformat())
                    elif hasattr(ts, "strftime"):
                        timestamps.append(ts.strftime("%Y-%m-%dT%H:%M:%SZ"))
                    else:
                        timestamps.append(str(ts) if ts else None)

            # Pad with nulls if less than 3 elements
            while len(timestamps) < 3:
                timestamps.append(None)

            return json.dumps(timestamps)
        except Exception as e:
            logger.warning(f"Failed to process EventTimeStamps: {e}")
            return None

    @staticmethod
    def process_event_message_texts(raw_messages) -> Optional[str]:
        """
        Convert BACnet EventMessageTexts array to JSON.

        Args:
            raw_messages: Array of 3 CharacterString objects

        Returns:
            JSON array of message strings

        Example:
            Input: ["High temperature alarm", "", "Temperature warning"]
            Output: '["High temperature alarm","","Temperature warning"]'
        """
        if raw_messages is None:
            return None

        try:
            import json

            messages = []

            # Process array of messages
            if hasattr(raw_messages, "__iter__"):
                for msg in raw_messages[:3]:  # Ensure max 3 elements
                    if msg is None:
                        messages.append("")
                    else:
                        messages.append(str(msg))

            # Pad with empty strings if less than 3 elements
            while len(messages) < 3:
                messages.append("")

            return json.dumps(messages)
        except Exception as e:
            logger.warning(f"Failed to process EventMessageTexts: {e}")
            return None

    @staticmethod
    def process_object_property_reference(raw_ref) -> Optional[str]:
        """
        Convert BACnet ObjectPropertyReference to JSON.

        Args:
            raw_ref: BACnet ObjectPropertyReference object

        Returns:
            JSON string with object and property identifiers

        Example:
            Input: ObjectPropertyReference(analogInput:1, presentValue)
            Output: '{"objectIdentifier":"analogInput:1","propertyIdentifier":"presentValue"}'
        """
        if raw_ref is None:
            return None

        try:
            import json

            ref_dict: Dict[str, Union[str, int, None]] = {}

            # Handle BACnet ObjectPropertyReference
            if hasattr(raw_ref, "objectIdentifier"):
                ref_dict["objectIdentifier"] = str(raw_ref.objectIdentifier)
            if hasattr(raw_ref, "propertyIdentifier"):
                ref_dict["propertyIdentifier"] = str(raw_ref.propertyIdentifier)
            if hasattr(raw_ref, "arrayIndex"):
                ref_dict["arrayIndex"] = (
                    int(raw_ref.arrayIndex) if raw_ref.arrayIndex is not None else None
                )

            return json.dumps(ref_dict) if ref_dict else None
        except Exception as e:
            logger.warning(f"Failed to process ObjectPropertyReference: {e}")
            return None

    @staticmethod
    def process_all_optional_properties(raw_properties: dict) -> dict:
        """
        Process all optional BACnet properties.

        Returns dict with processed properties ready for database storage.
        """
        return {
            # Value limits (simple Real values - no processing needed)
            "min_pres_value": raw_properties.get("minPresValue"),
            "max_pres_value": raw_properties.get("maxPresValue"),
            "high_limit": raw_properties.get("highLimit"),
            "low_limit": raw_properties.get("lowLimit"),
            "resolution": raw_properties.get("resolution"),
            # Control properties
            "priority_array": BACnetHealthProcessor.process_priority_array(
                raw_properties.get("priorityArray")
            ),
            "relinquish_default": raw_properties.get("relinquishDefault"),
            # Notification config
            "cov_increment": raw_properties.get("covIncrement"),
            "time_delay": raw_properties.get("timeDelay"),
            "time_delay_normal": raw_properties.get("timeDelayNormal"),
            "notification_class": raw_properties.get("notificationClass"),
            "notify_type": (
                str(raw_properties.get("notifyType"))
                if raw_properties.get("notifyType")
                else None
            ),
            "deadband": raw_properties.get("deadband"),
            "limit_enable": BACnetHealthProcessor.process_limit_enable(
                raw_properties.get("limitEnable")
            ),
            # Event properties
            "event_enable": BACnetHealthProcessor.process_event_transition_bits(
                raw_properties.get("eventEnable"), "eventEnable"
            ),
            "acked_transitions": BACnetHealthProcessor.process_event_transition_bits(
                raw_properties.get("ackedTransitions"), "ackedTransitions"
            ),
            "event_time_stamps": BACnetHealthProcessor.process_event_timestamps(
                raw_properties.get("eventTimeStamps")
            ),
            "event_message_texts": BACnetHealthProcessor.process_event_message_texts(
                raw_properties.get("eventMessageTexts")
            ),
            "event_message_texts_config": BACnetHealthProcessor.process_event_message_texts(
                raw_properties.get("eventMessageTextsConfig")
            ),
            # Algorithm control
            "event_detection_enable": (
                bool(raw_properties.get("eventDetectionEnable"))
                if raw_properties.get("eventDetectionEnable") is not None
                else None
            ),
            "event_algorithm_inhibit_ref": BACnetHealthProcessor.process_object_property_reference(
                raw_properties.get("eventAlgorithmInhibitRef")
            ),
            "event_algorithm_inhibit": (
                bool(raw_properties.get("eventAlgorithmInhibit"))
                if raw_properties.get("eventAlgorithmInhibit") is not None
                else None
            ),
            "reliability_evaluation_inhibit": (
                bool(raw_properties.get("reliabilityEvaluationInhibit"))
                if raw_properties.get("reliabilityEvaluationInhibit") is not None
                else None
            ),
        }
