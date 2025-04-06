CREATE OR REPLACE FUNCTION merge_or_insert(
    table_name text,
    data jsonb,
    primary_keys text[],
    unique_constraints text[]
) RETURNS void AS $$
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
    
    -- Build UPDATE clause for WHEN MATCHED
    update_clause := '';
    FOR column_name, column_value IN SELECT * FROM jsonb_each(data) LOOP
        -- Skip key columns in updates
        IF NOT (column_name = ANY(all_keys)) THEN
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
    
    -- Build source query for MERGE
    source_query := format('(SELECT 1 AS dummy) s');
    
    -- Construct the complete MERGE statement
    merge_query := format('
        MERGE INTO %I t
        USING %s
        ON %s
        WHEN MATCHED AND (%s IS NOT NULL) THEN
            UPDATE SET %s
        WHEN NOT MATCHED THEN
            INSERT %s',
        table_name,
        source_query,
        match_condition,
        CASE WHEN update_clause = '' THEN 'FALSE' ELSE 'TRUE' END,
        CASE WHEN update_clause = '' THEN 'dummy = dummy' ELSE update_clause END,
        insert_clause
    );
    
    -- Log the query for debugging (optional)
    RAISE NOTICE 'Executing: %', merge_query;
    
    -- Execute the MERGE statement
    EXECUTE merge_query;
END;
$$ LANGUAGE plpgsql;