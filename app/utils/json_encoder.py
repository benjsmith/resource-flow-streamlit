"""
Utility module for handling JSON encoding of objects that aren't natively JSON serializable,
such as datetime.timedelta.
"""
import json
from datetime import date, datetime, timedelta
from typing import Any

class ResourceFlowJSONEncoder(json.JSONEncoder):
    """
    A custom JSON encoder for the Resource Flow application that handles special types
    like timedelta objects.
    """
    
    def default(self, obj):
        """
        Convert objects that aren't natively JSON serializable.
        
        Args:
            obj: The object to encode
            
        Returns:
            A JSON serializable version of the object
        """
        if isinstance(obj, timedelta):
            # Convert timedelta to a string
            return str(obj)
        
        # Handle dates and datetimes
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        
        # Let the parent class handle it or raise TypeError
        return super().default(obj)

def json_dumps(obj):
    """
    Convenience function to dump an object to JSON string using our custom encoder.
    
    Args:
        obj: Object to encode as JSON
        
    Returns:
        JSON string representation
    """
    return json.dumps(obj, cls=ResourceFlowJSONEncoder) 