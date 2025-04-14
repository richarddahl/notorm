# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.sql.config import SQLConfig
from uno.sql.emitters.table import (
    AlterGrants,
    InsertMetaType,
)
from typing import List, Dict, Any, Optional
from uno.sql.builders import SQLIndexBuilder, SQLTriggerBuilder, SQLFunctionBuilder
from uno.sql.emitter import SQLEmitter
from uno.sql.statement import SQLStatement, SQLStatementType
from uno.sql.emitters.graph import GraphSQLEmitter
from uno.meta.models import MetaTypeModel, MetaRecordModel

# Custom CreateTable emitter for workflows module
class CreateTable(SQLEmitter):
    """Emitter for creating tables in the database."""
    
    # Model is needed as a field for pydantic
    model: Any = None
    _table: Optional[Any] = None
    
    def model_post_init(self, __context):
        """Called after pydantic initialization."""
        super().model_post_init(__context)
        if self.model:
            self._table = self.model.__table__
            
    @property
    def table(self):
        return self._table
        
    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL statement for creating the table.
        
        Returns:
            List of SQL statements with metadata
        """
        if self.table is None:
            return []
            
        # Use sqlalchemy's CreateTable DDL
        from sqlalchemy.schema import CreateTable as SQLACreateTable
        
        create_table_sql = str(SQLACreateTable(self.table))
        
        # Add statement to the list
        return [
            SQLStatement(
                name=f"create_{self.table.name}_table",
                type=SQLStatementType.TABLE,
                sql=create_table_sql,
            )
        ]

# Custom CreateIndex emitter for workflows module
class CreateIndex(SQLEmitter):
    """Emitter for creating indexes in the database."""
    
    # Fields for pydantic
    model: Any = None
    column_name: str = ""
    _table: Optional[Any] = None
    
    def model_post_init(self, __context):
        """Called after pydantic initialization."""
        super().model_post_init(__context)
        if self.model:
            self._table = self.model.__table__
            
    @property
    def table(self):
        return self._table
        
    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL statement for creating the index.
        
        Returns:
            List of SQL statements with metadata
        """
        if self.table is None:
            return []
            
        # Generate index name
        index_name = f"idx_{self.table.name}_{self.column_name}"
        
        # Generate create index SQL
        create_index_sql = f"""
        CREATE INDEX IF NOT EXISTS {index_name}
        ON {self.table.schema}.{self.table.name} ({self.column_name});
        """
        
        # Add statement to the list
        return [
            SQLStatement(
                name=f"create_{index_name}",
                type=SQLStatementType.INDEX,
                sql=create_index_sql,
            )
        ]
        
# Custom CreateEventTriggerFunction emitter for workflows module
class CreateEventTriggerFunction(SQLEmitter):
    """Emitter for creating event trigger functions."""
    
    # Fields for pydantic
    name: str = ""
    description: str = ""
    parameters: List[Dict[str, Any]] = []
    returns: str = "void"
    volatility: str = "VOLATILE"
    sql: str = ""
    
    @property
    def function_name(self):
        return self.name
        
    @property
    def function_sql(self):
        return self.sql
        
    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL statement for creating the event trigger function.
        
        Returns:
            List of SQL statements with metadata
        """
        # Format parameters
        params_str = ""
        if self.parameters:
            params_str = ", ".join([f"{param['name']} {param['type']}" for param in self.parameters])
            
        # Generate complete function SQL
        function_sql = f"""
        -- {self.description}
        CREATE OR REPLACE FUNCTION {self.config.DB_SCHEMA}.{self.function_name}({params_str})
        RETURNS {self.returns}
        LANGUAGE plpgsql
        {self.volatility}
        AS $function$
        {self.function_sql}
        $function$;
        """
        
        # Add statement to the list
        return [
            SQLStatement(
                name=f"create_{self.function_name}",
                type=SQLStatementType.FUNCTION,
                sql=function_sql,
            )
        ]
from uno.workflows.models import (
    WorkflowDefinition,
    WorkflowTriggerModel,
    WorkflowConditionModel,
    WorkflowActionModel,
    WorkflowRecipientModel,
    WorkflowExecutionLog,
)


# Create table objects before passing to SQLConfig to avoid positional argument issues
wf_table = WorkflowDefinition.__table__
wf_trigger_table = WorkflowTriggerModel.__table__
wf_condition_table = WorkflowConditionModel.__table__
wf_action_table = WorkflowActionModel.__table__
wf_recipient_table = WorkflowRecipientModel.__table__
wf_execution_table = WorkflowExecutionLog.__table__

# SQL configurations for workflow-related tables
workflow_sql_config = SQLConfig(
    emitters=[
        CreateTable(model=WorkflowDefinition),
        AlterGrants(table=wf_table),
        GraphSQLEmitter(
            source_model=WorkflowDefinition,
            target_model=MetaTypeModel,
            rel_name="DEFINES_WORKFLOW",
            rev_rel_name="IS_DEFINED_BY_WORKFLOW",
        ),
    ],
)

workflow_trigger_sql_config = SQLConfig(
    emitters=[
        CreateTable(model=WorkflowTriggerModel),
        AlterGrants(table=wf_trigger_table),
        CreateIndex(model=WorkflowTriggerModel, column_name="entity_type"),
    ],
)

workflow_condition_sql_config = SQLConfig(
    emitters=[
        CreateTable(model=WorkflowConditionModel),
        AlterGrants(table=wf_condition_table),
    ],
)

workflow_action_sql_config = SQLConfig(
    emitters=[
        CreateTable(model=WorkflowActionModel),
        AlterGrants(table=wf_action_table),
    ],
)

workflow_recipient_sql_config = SQLConfig(
    emitters=[
        CreateTable(model=WorkflowRecipientModel),
        AlterGrants(table=wf_recipient_table),
    ],
)

workflow_execution_log_sql_config = SQLConfig(
    emitters=[
        CreateTable(model=WorkflowExecutionLog),
        AlterGrants(table=wf_execution_table),
        CreateIndex(model=WorkflowExecutionLog, column_name="status"),
        CreateIndex(model=WorkflowExecutionLog, column_name="executed_at"),
    ],
)

# Event trigger function for database events that might trigger workflows
workflow_event_trigger_function = CreateEventTriggerFunction(
    name="workflow_event_trigger",
    description="Trigger function to capture database events for workflow processing",
    parameters=[],
    returns="trigger",
    volatility="VOLATILE",
    sql="""
    DECLARE
        payload JSONB;
        operation TEXT;
    BEGIN
        -- Determine operation type
        IF TG_OP = 'INSERT' THEN
            operation := 'Insert';
            payload := row_to_json(NEW)::JSONB;
        ELSIF TG_OP = 'UPDATE' THEN
            operation := 'Update';
            payload := jsonb_build_object(
                'old', row_to_json(OLD)::JSONB,
                'new', row_to_json(NEW)::JSONB,
                'changes', (
                    SELECT jsonb_object_agg(key, value)
                    FROM jsonb_each(row_to_json(NEW)::JSONB) AS t(key, value)
                    WHERE NOT (row_to_json(OLD)::JSONB ? key AND row_to_json(OLD)::JSONB ->> key = value::TEXT)
                )
            );
        ELSIF TG_OP = 'DELETE' THEN
            operation := 'Delete';
            payload := row_to_json(OLD)::JSONB;
        END IF;
        
        -- Construct event data
        PERFORM pg_notify('workflow_events', jsonb_build_object(
            'table_name', TG_TABLE_NAME,
            'schema_name', TG_TABLE_SCHEMA,
            'operation', operation,
            'timestamp', extract(epoch from clock_timestamp()),
            'payload', payload
        )::TEXT);
        
        -- Return appropriate record based on operation
        IF TG_OP = 'DELETE' THEN
            RETURN OLD;
        ELSE
            RETURN NEW;
        END IF;
    END;
    """,
)

# Create workflow process function that will be called from event listener
workflow_process_function = CreateEventTriggerFunction(
    name="process_workflow_event",
    description="Process a workflow event and execute appropriate workflows",
    parameters=[
        {"name": "event_data", "type": "JSONB"},
    ],
    returns="JSONB",
    volatility="VOLATILE",
    sql="""
    DECLARE
        matching_triggers RECORD;
        workflow_record RECORD;
        execution_id TEXT;
        execution_status TEXT := 'pending';
        execution_result JSONB := '{}'::JSONB;
        execution_error TEXT := NULL;
        start_time TIMESTAMPTZ;
        end_time TIMESTAMPTZ;
        duration_ms FLOAT;
    BEGIN
        -- Start timing
        start_time := clock_timestamp();
        
        -- Find matching workflow triggers
        FOR matching_triggers IN (
            SELECT 
                wt.id AS trigger_id,
                wt.workflow_id,
                wd.name AS workflow_name,
                wt.field_conditions
            FROM 
                workflow_trigger wt
                JOIN workflow_definition wd ON wt.workflow_id = wd.id
            WHERE 
                wt.is_active = TRUE
                AND wd.status = 'active'
                AND wt.entity_type = (event_data->>'table_name')
                AND wt.operation = (event_data->>'operation')
            ORDER BY 
                wt.priority ASC
        ) LOOP
            -- Log execution start
            execution_id := gen_ulid();
            INSERT INTO workflow_execution_log (
                id, workflow_id, trigger_event_id, status, executed_at, context
            ) VALUES (
                execution_id,
                matching_triggers.workflow_id,
                (event_data->>'timestamp')::TEXT,
                'pending',
                clock_timestamp(),
                event_data
            );
            
            -- TODO: Evaluate workflow conditions
            
            -- TODO: Execute workflow actions
            
            -- For now, just log that we found a matching workflow
            execution_status := 'success';
            execution_result := jsonb_build_object(
                'workflow_id', matching_triggers.workflow_id,
                'workflow_name', matching_triggers.workflow_name,
                'matched_trigger', matching_triggers.trigger_id
            );
            
            -- End timing
            end_time := clock_timestamp();
            duration_ms := extract(epoch from (end_time - start_time)) * 1000;
            
            -- Update execution log
            UPDATE workflow_execution_log
            SET 
                status = execution_status,
                completed_at = end_time,
                result = execution_result,
                error = execution_error,
                execution_time = duration_ms
            WHERE 
                id = execution_id;
        END LOOP;
        
        RETURN jsonb_build_object(
            'status', 'processed',
            'matched_workflows', execution_result
        );
    END;
    """,
)

# Combined SQL config for workflow module
workflow_module_sql_config = [
    workflow_sql_config,
    workflow_trigger_sql_config,
    workflow_condition_sql_config,
    workflow_action_sql_config,
    workflow_recipient_sql_config,
    workflow_execution_log_sql_config,
    workflow_event_trigger_function,
    workflow_process_function,
]
