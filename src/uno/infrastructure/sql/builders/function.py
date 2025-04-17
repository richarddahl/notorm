# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""SQL function builder."""

class SQLFunctionBuilder:
    """Builder for SQL functions.
    
    This class provides a fluent interface for building SQL function
    statements with proper validation and formatting.
    
    Example:
        ```python
        function_sql = (
            SQLFunctionBuilder()
            .with_schema("public")
            .with_name("my_function")
            .with_args("value text")
            .with_return_type("boolean")
            .with_body("BEGIN RETURN true; END;")
            .build()
        )
        ```
    """
    def __init__(self):
        """Initialize the SQL function builder."""
        self.schema = None
        self.name = None
        self.args = ""
        self.return_type = "TRIGGER"
        self.body = None
        self.language = "plpgsql"
        self.volatility = "VOLATILE"
        self.security_definer = False
        self.db_name = None
        self.auto_set_admin_role = True
        
    def with_schema(self, schema: str) -> "SQLFunctionBuilder":
        """Set the schema for the function.
        
        Args:
            schema: Schema name
            
        Returns:
            Self for method chaining
        """
        self.schema = schema
        return self
        
    def with_name(self, name: str) -> "SQLFunctionBuilder":
        """Set the name of the function.
        
        Args:
            name: Function name
            
        Returns:
            Self for method chaining
        """
        self.name = name
        return self
        
    def with_args(self, args: str) -> "SQLFunctionBuilder":
        """Set the arguments for the function.
        
        Args:
            args: Function arguments as a string
            
        Returns:
            Self for method chaining
        """
        self.args = args
        return self
        
    def with_return_type(self, return_type: str) -> "SQLFunctionBuilder":
        """Set the return type for the function.
        
        Args:
            return_type: Function return type
            
        Returns:
            Self for method chaining
        """
        self.return_type = return_type
        return self
        
    def with_body(self, body: str) -> "SQLFunctionBuilder":
        """Set the function body.
        
        Args:
            body: Function implementation body
            
        Returns:
            Self for method chaining
        """
        self.body = body
        return self
        
    def with_language(self, language: str) -> "SQLFunctionBuilder":
        """Set the function language.
        
        Args:
            language: Function language (e.g. 'plpgsql', 'sql')
            
        Returns:
            Self for method chaining
        """
        self.language = language
        return self
        
    def with_volatility(self, volatility: str) -> "SQLFunctionBuilder":
        """Set the function volatility.
        
        Args:
            volatility: Function volatility ('VOLATILE', 'STABLE', or 'IMMUTABLE')
            
        Returns:
            Self for method chaining
            
        Raises:
            ValueError: If volatility is not valid
        """
        valid_volatilities = ["VOLATILE", "STABLE", "IMMUTABLE"]
        if volatility not in valid_volatilities:
            raise ValueError(f"Invalid volatility: {volatility}. Must be one of {valid_volatilities}")
        
        self.volatility = volatility
        return self
        
    def as_security_definer(self) -> "SQLFunctionBuilder":
        """Set the function to use SECURITY DEFINER.
        
        Returns:
            Self for method chaining
        """
        self.security_definer = True
        return self
        
    def with_db_name(self, db_name: str) -> "SQLFunctionBuilder":
        """Set the database name for automatic role handling.
        
        Args:
            db_name: Database name
            
        Returns:
            Self for method chaining
        """
        self.db_name = db_name
        return self
        
    def with_auto_role(self, enabled: bool = True) -> "SQLFunctionBuilder":
        """Set whether to automatically add admin role setter to function body.
        
        Args:
            enabled: Whether to automatically add role setter
            
        Returns:
            Self for method chaining
        """
        self.auto_set_admin_role = enabled
        return self
    
    def build(self) -> str:
        """Build the SQL function statement.
        
        Returns:
            SQL function statement
            
        Raises:
            ValueError: If required parameters are missing
        """
        if not self.schema or not self.name or not self.body:
            raise ValueError("Schema, name, and body are required for a function")
        
        # Process the function body to add admin role if requested
        body = self.body
        if self.auto_set_admin_role and self.db_name:
            admin_role = f"{self.db_name}_admin"
            
            # Check if the body already contains a SET ROLE statement
            if not any(line.strip().startswith('SET ROLE') for line in body.splitlines()):
                # Add the SET ROLE statement after BEGIN if present, otherwise at the start
                if 'BEGIN' in body:
                    body = body.replace('BEGIN', f'BEGIN\n    SET ROLE {admin_role};', 1)
                else:
                    body = f"SET ROLE {admin_role};\n{body}"
            
        security = "SECURITY DEFINER" if self.security_definer else ""
        
        return f"""
            CREATE OR REPLACE FUNCTION {self.schema}.{self.name}({self.args})
            RETURNS {self.return_type}
            LANGUAGE {self.language}
            {self.volatility}
            {security}
            AS $fnct$
            {body}
            $fnct$;
        """