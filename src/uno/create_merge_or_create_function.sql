CREATE OR REPLACE FUNCTION merge_or_insert(
    table_name text,
    data jsonb,
    primary_keys text[],
    unique_constraints text[]
) RETURNS jsonb AS $$
DECLARE
    merge_query text;
    source_query text;
    match_condition text;
    update_clause text;
    insert_clause text;
    column_name text;
    column_value jsonb;
    all_keys text[];
    pk_condition text;
    unique_condition text;
    match_type text;
    has_pk boolean;
    has_unique boolean;
    result_record jsonb;
    select_query text;
    existing_record jsonb;
    action_performed text;
    existing_record_count integer;
    needs_update boolean;
    update_condition text;
BEGIN
    -- Validate inputs
    IF table_name IS NULL OR data IS NULL THEN
        RAISE EXCEPTION 'Invalid parameters: table_name and data must be provided';
    END IF;
    
    -- Check if we have primary keys and/or unique constraints
    has_pk := array_length(primary_keys, 1) > 0 AND 
              (SELECT bool_and(data ? key) FROM unnest(primary_keys) AS key);
    
    has_unique := array_length(unique_constraints, 1) > 0 AND 
                  (SELECT bool_and(data ? key) FROM unnest(unique_constraints) AS key);
    
    -- Determine which keys to use for matching
    IF has_pk THEN
        all_keys := primary_keys;
        match_type := 'primary keys';
    ELSIF has_unique THEN
        all_keys := unique_constraints;
        match_type := 'unique constraints';
    ELSE
        RAISE EXCEPTION 'Neither primary keys nor unique constraints are available in the data';
    END IF;
    
    -- Build match condition based on the keys
    match_condition := '';
    FOREACH column_name IN ARRAY all_keys LOOP
        IF data ? column_name THEN
            IF match_condition != '' THEN
                match_condition := match_condition || ' AND ';
            END IF;
            
            -- Handle different data types appropriately
            IF jsonb_typeof(data->column_name) = 'string' THEN
                match_condition := match_condition || format('t.%I = %L', 
                                                           column_name, 
                                                           data->>column_name);
            ELSIF jsonb_typeof(data->column_name) = 'number' THEN
                match_condition := match_condition || format('t.%I = %s', 
                                                           column_name, 
                                                           data->>column_name);
            ELSIF jsonb_typeof(data->column_name) = 'boolean' THEN
                match_condition := match_condition || format('t.%I = %s', 
                                                           column_name, 
                                                           data->>column_name);
            ELSIF jsonb_typeof(data->column_name) = 'null' THEN
                match_condition := match_condition || format('t.%I IS NULL', 
                                                           column_name);
            ELSE
                -- For complex types like arrays, objects
                match_condition := match_condition || format('t.%I = %L::jsonb', 
                                                           column_name, 
                                                           data->column_name);
            END IF;
        ELSE
            RAISE EXCEPTION 'Required % column "%" not found in data', match_type, column_name;
        END IF;
    END LOOP;
    
    -- Check if the record already exists and get its current state
    select_query := format('
        SELECT to_jsonb(t.*) 
        FROM %I t 
        WHERE %s',
        table_name,
        match_condition
    );
    
    EXECUTE select_query INTO existing_record;
    existing_record_count := CASE WHEN existing_record IS NOT NULL THEN 1 ELSE 0 END;
    
    -- Build UPDATE clause and update condition for WHEN MATCHED
    update_clause := '';
    update_condition := '';
    
    FOR column_name, column_value IN SELECT * FROM jsonb_each(data) LOOP
        -- Skip key columns in updates
        IF NOT (column_name = ANY(all_keys)) THEN
            -- Check if the value is different from the existing record
            IF existing_record_count > 0 AND existing_record ? column_name THEN
                -- Compare the values to see if an update is needed
                IF (jsonb_typeof(column_value) = 'null' AND jsonb_typeof(existing_record->column_name) <> 'null') OR
                   (jsonb_typeof(column_value) <> 'null' AND jsonb_typeof(existing_record->column_name) = 'null') OR
                   (jsonb_typeof(column_value) <> 'null' AND jsonb_typeof(existing_record->column_name) <> 'null' AND 
                    column_value <> existing_record->column_name) THEN
                    
                    -- Value is different, add to update condition
                    IF update_condition != '' THEN
                        update_condition := update_condition || ' OR ';
                    END IF;
                    
                    -- Add this column to the update condition
                    IF jsonb_typeof(column_value) = 'null' THEN
                        update_condition := update_condition || format('t.%I IS NOT NULL', column_name);
                    ELSIF jsonb_typeof(existing_record->column_name) = 'null' THEN
                        update_condition := update_condition || format('t.%I IS NULL', column_name);
                    ELSE
                        update_condition := update_condition || format('t.%I <> %L', 
                                                                    column_name, 
                                                                    column_value#>>'{}');
                    END IF;
                END IF;
            END IF;
            
            -- Always build the update clause
            IF update_clause != '' THEN
                update_clause := update_clause || ', ';
            END IF;
            
            -- Handle different data types appropriately
            IF jsonb_typeof(column_value) = 'string' THEN
                update_clause := update_clause || format('%I = %L', 
                                                       column_name, 
                                                       column_value#>>'{}');
            ELSIF jsonb_typeof(column_value) = 'number' THEN
                update_clause := update_clause || format('%I = %s', 
                                                       column_name, 
                                                       column_value#>>'{}');
            ELSIF jsonb_typeof(column_value) = 'boolean' THEN
                update_clause := update_clause || format('%I = %s', 
                                                       column_name, 
                                                       column_value#>>'{}');
            ELSIF jsonb_typeof(column_value) = 'null' THEN
                update_clause := update_clause || format('%I = NULL', 
                                                       column_name);
            ELSE
                -- For complex types like arrays, objects
                update_clause := update_clause || format('%I = %L::jsonb', 
                                                       column_name, 
                                                       column_value);
            END IF;
        END IF;
    END LOOP;
    
    -- If update_condition is empty but update_clause isn't, it means all values are the same
    needs_update := update_condition <> '';
    
    -- Build INSERT clause for WHEN NOT MATCHED
    insert_clause := '';
    DECLARE
        columns text := '';
        values text := '';
    BEGIN
        FOR column_name, column_value IN SELECT * FROM jsonb_each(data) LOOP
            IF columns != '' THEN
                columns := columns || ', ';
                values := values || ', ';
            END IF;
            
            columns := columns || format('%I', column_name);
            
            -- Handle different data types appropriately
            IF jsonb_typeof(column_value) = 'string' THEN
                values := values || format('%L', column_value#>>'{}');
            ELSIF jsonb_typeof(column_value) = 'number' THEN
                values := values || format('%s', column_value#>>'{}');
            ELSIF jsonb_typeof(column_value) = 'boolean' THEN
                values := values || format('%s', column_value#>>'{}');
            ELSIF jsonb_typeof(column_value) = 'null' THEN
                values := values || 'NULL';
            ELSE
                -- For complex types like arrays, objects
                values := values || format('%L::jsonb', column_value);
            END IF;
        END LOOP;
        
        insert_clause := format('(%s) VALUES (%s)', columns, values);
    END;
    -- Set the action based on whether the record exists and needs update
    IF existing_record_count > 0 THEN
        IF needs_update THEN
            action_performed := 'updated';
        ELSE
            action_performed := 'retrieved';
        END IF;
    ELSE
        action_performed := 'created';
    END IF;
    
    -- Build source query for MERGE
    source_query := format('(SELECT 1 AS dummy) s');
    
    -- Construct the complete MERGE statement
    IF existing_record_count > 0 AND needs_update THEN
        -- Record exists and needs update
        merge_query := format('
            MERGE INTO %I t
            USING %s
            ON %s
            WHEN MATCHED THEN
                UPDATE SET %s',
            table_name,
            source_query,
            match_condition,
            update_clause
        );
    ELSIF existing_record_count = 0 THEN
        -- Record doesn't exist, insert it
        merge_query := format('
            MERGE INTO %I t
            USING %s
            ON %s
            WHEN NOT MATCHED THEN
                INSERT %s',
            table_name,
            source_query,
            match_condition,
            insert_clause
        );
    ELSE
        -- Record exists and doesn't need update, do nothing
        merge_query := NULL;
    END IF;
    
    -- Execute the MERGE statement if needed
    IF merge_query IS NOT NULL THEN
        EXECUTE merge_query;
    END IF;
    
    -- Get the final record
    EXECUTE select_query INTO result_record;
    
    -- Add the action performed to the result
    result_record := jsonb_set(result_record, '{_action}', to_jsonb(action_performed));
    
    -- Return the result
    RETURN result_record;
END;
$$ LANGUAGE plpgsql;