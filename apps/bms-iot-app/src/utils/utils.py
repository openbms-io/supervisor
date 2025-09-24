from typing import Optional, Dict, Union, List, Tuple

from bacpypes3.basetypes import PriorityValue, TimeStamp


def kebab_to_camel(kebab_str: str) -> str:
    parts = kebab_str.split("-")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


def normalize_value(
    value: Union[str, int, float, bool, List, object],
) -> Union[str, int, float, bool, List, Dict, None]:
    # Handle lists/arrays of BACnet objects (like PriorityArray)
    if isinstance(value, list):
        return [normalize_value(item) for item in value]

    # Handle PriorityValue objects using dedicated normalization function
    if hasattr(value, "__class__") and "PriorityValue" in str(value.__class__):
        return normalize_priority_value(value)

    # Handle TimeStamp objects using dedicated normalization function
    if hasattr(value, "__class__") and "TimeStamp" in str(value.__class__):
        return normalize_timestamp(value)

    # Handle other BACnet objects that have specific attributes
    if hasattr(value, "value"):
        return value.value
    if hasattr(value, "asn1"):
        return str(value.asn1)  # Ensure JSON-safe string
    if hasattr(value, "dict_contents"):
        return dict(value.dict_contents())  # Force to plain dict
    if isinstance(value, tuple) and hasattr(value[0], "asn1"):  # (ObjectType, int)
        return (str(value[0].asn1), value[1])
    return value  # fallback for float, str, etc.


def normalize_priority_value(
    value: Optional[Union[PriorityValue, None]],
) -> Optional[Dict[str, Union[str, int, float, bool, Dict, None]]]:
    """
    Normalize a PriorityValue object to a JSON-serializable dict.

    Handles all 14 PriorityValue Choice types:
    - null, real, boolean, unsigned, integer, double, time, characterString,
    - octetString, bitString, enumerated, date, objectIdentifier, constructedValue

    Args:
        value: PriorityValue object or None

    Returns:
        dict: {"type": <type>, "value": <normalized_value>} or None for None input
    """
    if value is None:
        return None

    # Check if it's actually a PriorityValue object
    if not (
        hasattr(value, "__class__") and "PriorityValue" in value.__class__.__name__
    ):
        return {"type": "error", "value": "Not a PriorityValue object"}

    try:
        # Check each PriorityValue type in order of most common usage
        if hasattr(value, "real") and value.real is not None:
            return {"type": "real", "value": float(value.real)}

        elif hasattr(value, "null") and value.null is not None:
            return {"type": "null", "value": None}

        elif hasattr(value, "boolean") and value.boolean is not None:
            return {"type": "boolean", "value": bool(value.boolean)}

        elif hasattr(value, "unsigned") and value.unsigned is not None:
            return {"type": "unsigned", "value": int(value.unsigned)}

        elif hasattr(value, "integer") and value.integer is not None:
            return {"type": "integer", "value": int(value.integer)}

        elif hasattr(value, "double") and value.double is not None:
            return {"type": "double", "value": float(value.double)}

        elif hasattr(value, "time") and value.time is not None:
            time_obj = value.time
            time_dict = {}
            if hasattr(time_obj, "hour"):
                time_dict["hour"] = time_obj.hour
            if hasattr(time_obj, "minute"):
                time_dict["minute"] = time_obj.minute
            if hasattr(time_obj, "second"):
                time_dict["second"] = time_obj.second
            if hasattr(time_obj, "hundredth"):
                time_dict["hundredth"] = time_obj.hundredth
            return {"type": "time", "value": time_dict}

        elif hasattr(value, "characterString") and value.characterString is not None:
            return {"type": "characterString", "value": str(value.characterString)}

        elif hasattr(value, "octetString") and value.octetString is not None:
            # Convert bytes to list of integers for JSON serialization
            octet_data = value.octetString
            if isinstance(octet_data, bytes):
                return {"type": "octetString", "value": list(octet_data)}
            else:
                return {"type": "octetString", "value": str(octet_data)}

        elif hasattr(value, "bitString") and value.bitString is not None:
            return {"type": "bitString", "value": str(value.bitString)}

        elif hasattr(value, "enumerated") and value.enumerated is not None:
            return {"type": "enumerated", "value": int(value.enumerated)}

        elif hasattr(value, "date") and value.date is not None:
            date_obj = value.date
            date_dict = {}
            if hasattr(date_obj, "year"):
                date_dict["year"] = date_obj.year
            if hasattr(date_obj, "month"):
                date_dict["month"] = date_obj.month
            if hasattr(date_obj, "day"):
                date_dict["day"] = date_obj.day
            return {"type": "date", "value": date_dict}

        elif hasattr(value, "objectIdentifier") and value.objectIdentifier is not None:
            obj_id = value.objectIdentifier
            obj_dict = {}
            if hasattr(obj_id, "objectType"):
                obj_dict["objectType"] = str(obj_id.objectType)
            if hasattr(obj_id, "instanceNumber"):
                obj_dict["instanceNumber"] = int(obj_id.instanceNumber)
            return {"type": "objectIdentifier", "value": obj_dict}

        elif hasattr(value, "constructedValue") and value.constructedValue is not None:
            return {"type": "constructedValue", "value": str(value.constructedValue)}

        else:
            # All attributes are None - unknown type
            return {"type": "unknown", "value": str(value)}

    except Exception:
        return {"type": "error", "value": str(value)}


def normalize_timestamp(
    value: Optional[Union[TimeStamp, None]],
) -> Optional[Dict[str, Union[str, int]]]:
    """
    Normalize a TimeStamp object to a JSON-serializable dict.

    Handles all 3 TimeStamp Choice types:
    - time (context=0), sequenceNumber (context=1), dateTime (context=2)

    Args:
        value: TimeStamp object or None

    Returns:
        dict: {"type": <type>, "value": <normalized_value>} or None for None input
    """
    if value is None:
        return None

    # Check if it's actually a TimeStamp object
    if not (hasattr(value, "__class__") and "TimeStamp" in value.__class__.__name__):
        return {"type": "error", "value": "Not a TimeStamp object"}

    try:
        # Check each TimeStamp type and convert to ISO format for cleaner JSON
        if hasattr(value, "time") and value.time is not None:
            time_obj = value.time
            # Use isoformat() for clean ISO time string
            if hasattr(time_obj, "isoformat"):
                return {"type": "time", "value": time_obj.isoformat()}
            else:
                # Fallback to string representation
                return {"type": "time", "value": str(time_obj)}

        elif hasattr(value, "sequenceNumber") and value.sequenceNumber is not None:
            return {"type": "sequenceNumber", "value": int(value.sequenceNumber)}

        elif hasattr(value, "dateTime") and value.dateTime is not None:
            dt_obj = value.dateTime
            # Use isoformat() for clean ISO datetime string
            if hasattr(dt_obj, "isoformat"):
                return {"type": "dateTime", "value": dt_obj.isoformat()}
            else:
                # Fallback to string representation
                return {"type": "dateTime", "value": str(dt_obj)}

        else:
            # All attributes are None - unknown type
            return {"type": "unknown", "value": str(value)}

    except Exception:
        return {"type": "error", "value": str(value)}


def extract_property_dict_camel(
    prop_tuples: List[Tuple],
) -> Dict[str, Union[str, int, float, bool, Dict, None]]:
    result = {}
    for value, prop_id in prop_tuples:
        raw_key = prop_id.asn1 if hasattr(prop_id, "asn1") else str(prop_id)
        camel_key = kebab_to_camel(raw_key)
        result[camel_key] = normalize_value(value)
    return result
