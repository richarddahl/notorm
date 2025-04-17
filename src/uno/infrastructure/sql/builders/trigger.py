# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""SQL trigger builder."""

class SQLTriggerBuilder:
    """Builder for SQL triggers.
    
    This class provides a fluent interface for building SQL trigger
    statements with proper validation and formatting.
    
    Example:
        ```python
        trigger_sql = (
            SQLTriggerBuilder()
            .with_schema("public")
            .with_table("users")
            .with_name("update_timestamp_trigger")
            .with_function("update_timestamp")
            .with_timing("BEFORE")
            .with_operation("INSERT OR UPDATE")
            .build()
        )
        ```
    """
    def __init__(self):
        """Initialize the SQL trigger builder."""
        self.schema = None
        self.table_name = None
        self.trigger_name = None
        self.function_name = None
        self.timing = "BEFORE"
        self.operation = "UPDATE"
        self.for_each = "ROW"
        
    def with_schema(self, schema: str) -> "SQLTriggerBuilder":
        """Set the schema for the trigger.
        
        Args:
            schema: Schema name
            
        Returns:
            Self for method chaining
        """
        self.schema = schema
        return self
        
    def with_table(self, table_name: str) -> "SQLTriggerBuilder":
        """Set the table for the trigger.
        
        Args:
            table_name: Table name
            
        Returns:
            Self for method chaining
        """
        self.table_name = table_name
        return self
        
    def with_name(self, trigger_name: str) -> "SQLTriggerBuilder":
        """Set the name of the trigger.
        
        Args:
            trigger_name: Trigger name
            
        Returns:
            Self for method chaining
        """
        self.trigger_name = trigger_name
        return self
        
    def with_function(self, function_name: str) -> "SQLTriggerBuilder":
        """Set the function to be called by the trigger.
        
        Args:
            function_name: Function name
            
        Returns:
            Self for method chaining
        """
        self.function_name = function_name
        return self
        
    def with_timing(self, timing: str) -> "SQLTriggerBuilder":
        """Set the timing for the trigger.
        
        Args:
            timing: Timing ('BEFORE', 'AFTER', or 'INSTEAD OF')
            
        Returns:
            Self for method chaining
            
        Raises:
            ValueError: If timing is not valid
        """
        valid_timings = ["BEFORE", "AFTER", "INSTEAD OF"]
        if timing not in valid_timings:
            raise ValueError(f"Invalid timing: {timing}. Must be one of {valid_timings}")
        self.timing = timing
        return self
        
    def with_operation(self, operation: str) -> "SQLTriggerBuilder":
        """Set the operation(s) for the trigger.
        
        Args:
            operation: Operation ('INSERT', 'UPDATE', 'DELETE', 'TRUNCATE')
                      or composite operations like 'INSERT OR UPDATE'
            
        Returns:
            Self for method chaining
            
        Raises:
            ValueError: If operation is not valid
        """
        base_operations = {"INSERT", "UPDATE", "DELETE", "TRUNCATE"}
        operations = [op.strip() for op in operation.split("OR")]
        if not all(op in base_operations for op in operations):
            raise ValueError(f"Invalid operation(s): {operation}")
        self.operation = operation
        return self
        
    def with_for_each(self, for_each: str) -> "SQLTriggerBuilder":
        """Set the for_each clause for the trigger.
        
        Args:
            for_each: For each ('ROW' or 'STATEMENT')
            
        Returns:
            Self for method chaining
            
        Raises:
            ValueError: If for_each is not valid
        """
        valid_for_each = ["ROW", "STATEMENT"]
        if for_each not in valid_for_each:
            raise ValueError(f"Invalid for_each: {for_each}. Must be one of {valid_for_each}")
        self.for_each = for_each
        return self
    
    def build(self) -> str:
        """Build the SQL trigger statement.
        
        Returns:
            SQL trigger statement
            
        Raises:
            ValueError: If required parameters are missing
        """
        if not self.schema or not self.table_name or not self.trigger_name or not self.function_name:
            raise ValueError("Schema, table name, trigger name, and function name are required")
            
        return f"""
            CREATE OR REPLACE TRIGGER {self.trigger_name}
                {self.timing} {self.operation}
                ON {self.schema}.{self.table_name}
                FOR EACH {self.for_each}
                EXECUTE FUNCTION {self.schema}.{self.function_name}();
        """
