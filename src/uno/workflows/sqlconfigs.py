# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.sql.classes import SQLConfig
from uno.sql.emitters.table import (
    AlterGrants,
    InsertMetaType,
    CreateTable,
    CreateIndex,
)
from uno.sql.emitters.triggers import (
    CreateTrigger,
    CreateEventTriggerFunction,
)
from uno.sql.emitters.graph import GraphSQLEmitter
from uno.meta.models import MetaTypeModel, MetaRecordModel
from uno.workflows.models import (
    WorkflowDefinition,
    WorkflowTriggerModel,
    WorkflowConditionModel,
    WorkflowActionModel,
    WorkflowRecipientModel,
    WorkflowExecutionLog,
)


# SQL configurations for workflow-related tables
workflow_sql_config = SQLConfig(
    model=WorkflowDefinition,
    emitters=[
        CreateTable(WorkflowDefinition),
        AlterGrants(WorkflowDefinition),
        GraphSQLEmitter(
            WorkflowDefinition,
            MetaTypeModel,
            "DEFINES_WORKFLOW",
            "IS_DEFINED_BY_WORKFLOW",
        ),
    ],
)

workflow_trigger_sql_config = SQLConfig(
    model=WorkflowTriggerModel,
    emitters=[
        CreateTable(WorkflowTriggerModel),
        AlterGrants(WorkflowTriggerModel),
        CreateIndex(WorkflowTriggerModel, "entity_type"),
    ],
)

workflow_condition_sql_config = SQLConfig(
    model=WorkflowConditionModel,
    emitters=[
        CreateTable(WorkflowConditionModel),
        AlterGrants(WorkflowConditionModel),
    ],
)

workflow_action_sql_config = SQLConfig(
    model=WorkflowActionModel,
    emitters=[
        CreateTable(WorkflowActionModel),
        AlterGrants(WorkflowActionModel),
    ],
)

workflow_recipient_sql_config = SQLConfig(
    model=WorkflowRecipientModel,
    emitters=[
        CreateTable(WorkflowRecipientModel),
        AlterGrants(WorkflowRecipientModel),
    ],
)

workflow_execution_log_sql_config = SQLConfig(
    model=WorkflowExecutionLog,
    emitters=[
        CreateTable(WorkflowExecutionLog),
        AlterGrants(WorkflowExecutionLog),
        CreateIndex(WorkflowExecutionLog, "status"),
        CreateIndex(WorkflowExecutionLog, "executed_at"),
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
