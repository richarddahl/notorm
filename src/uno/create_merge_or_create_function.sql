CREATE OR REPLACE FUNCTION merge_or_insert(
    table_name text,
    data jsonb
) RETURNS jsonb AS $$
DECLARE
    match_condition text := '';
    update_clause text := '';
    insert_columns text := '';
    insert_values text := '';
    primary_keys text[] := '{}';
    unique_constraints text[][] := '{}';
    all_keys text[];
    existing_record jsonb;
    action_performed text;
    needs_update boolean := false;
    column_name text;
    column_value jsonb;
    schema_name text := 'public';
    table_parts text[];
    qualified_table text;
    i integer;
    found_constraint text[];
    debug_info jsonb;
    data_keys text[];
    has_all_columns boolean;
BEGIN
    -- Validate inputs
    IF table_name IS NULL OR data IS NULL THEN
        RAISE EXCEPTION 'Invalid parameters: table_name and data must be provided';
    END IF;
    
    -- Extract schema if provided in table_name (schema.table format)
    IF position('.' in table_name) > 0 THEN
        table_parts := string_to_array(table_name, '.');
        schema_name := table_parts[1];
        table_name := table_parts[2];
        qualified_table := quote_ident(schema_name) || '.' || quote_ident(table_name);
    ELSE
        qualified_table := quote_ident(table_name);
    END IF;

    -- Get all keys from the data
    SELECT array_agg(key) INTO data_keys FROM jsonb_object_keys(data) AS key;

    -- Get primary keys
    SELECT array_agg(a.attname::text) INTO primary_keys
    FROM pg_index i
    JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
    WHERE i.indrelid = (schema_name || '.' || table_name)::regclass
    AND i.indisprimary;
    
    -- Check if primary keys are usable
    IF primary_keys IS NOT NULL AND array_length(primary_keys, 1) > 0 THEN
        -- Check if all primary key columns are in the data
        has_all_columns := true;
        
        FOREACH column_name IN ARRAY primary_keys LOOP
            IF NOT data ? column_name THEN
                has_all_columns := false;
                EXIT;
            END IF;
        END LOOP;
        
        IF has_all_columns THEN
            all_keys := primary_keys;
        END IF;
    END IF;

    -- If primary keys aren't usable, get unique constraints
    IF all_keys IS NULL THEN
        -- Get unique constraints
        WITH unique_idx AS (
            SELECT 
                i.indexrelid,
                array_agg(a.attname::text ORDER BY array_position(i.indkey, a.attnum)) as cols
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = (schema_name || '.' || table_name)::regclass
            AND i.indisunique AND NOT i.indisprimary
            GROUP BY i.indexrelid
        )
        SELECT array_agg(cols) INTO unique_constraints
        FROM unique_idx;
        
        -- Try each unique constraint
        IF unique_constraints IS NOT NULL AND array_length(unique_constraints, 1) > 0 THEN
            FOR i IN 1..array_length(unique_constraints, 1) LOOP
                found_constraint := unique_constraints[i];
                
                IF found_constraint IS NOT NULL AND array_length(found_constraint, 1) > 0 THEN
                    -- Check if all columns in this constraint are in the data
                    has_all_columns := true;
                    
                    FOREACH column_name IN ARRAY found_constraint LOOP
                        IF NOT data ? column_name THEN
                            has_all_columns := false;
                            EXIT;
                        END IF;
                    END LOOP;
                    
                    -- If we found a usable constraint, use it
                    IF has_all_columns THEN
                        all_keys := found_constraint;
                        EXIT;
                    END IF;
                END IF;
            END LOOP;
        END IF;
    END IF;

    -- Special case for single-column unique constraints
    IF all_keys IS NULL AND unique_constraints IS NOT NULL AND array_length(unique_constraints, 1) > 0 THEN
        -- Try each unique constraint again, but focus on single-column constraints
        FOR i IN 1..array_length(unique_constraints, 1) LOOP
            found_constraint := unique_constraints[i];
            
            IF found_constraint IS NOT NULL AND array_length(found_constraint, 1) = 1 THEN
                column_name := found_constraint[1];
                
                IF data ? column_name THEN
                    all_keys := ARRAY[column_name];
                    EXIT;
                END IF;
            END IF;
        END LOOP;
    END IF;

    -- Create debug info
    debug_info := jsonb_build_object(
        'table', table_name,
        'schema', schema_name,
        'data_keys', to_jsonb(data_keys),
        'primary_keys', to_jsonb(primary_keys),
        'unique_constraints', to_jsonb(unique_constraints),
        'selected_keys', to_jsonb(all_keys)
    );

    -- Raise exception if no usable keys found
    IF all_keys IS NULL OR array_length(all_keys, 1) = 0 THEN
        RAISE EXCEPTION 'No primary keys or unique constraints found in the data. Ensure that the data includes at least one primary key or unique constraint. Debug: %', debug_info;
    END IF;

    -- Build match condition
    FOREACH column_name IN ARRAY all_keys LOOP
        IF match_condition != '' THEN
            match_condition := match_condition || ' AND ';
        END IF;
        match_condition := match_condition || format('t.%I = %s', column_name, 
            CASE 
                WHEN jsonb_typeof(data->column_name) = 'null' THEN 'NULL'
                ELSE format('%L', data->>column_name)
            END);
    END LOOP;

    -- Execute the rest of the function as provided
    EXECUTE format('SELECT to_jsonb(t.*) FROM %s t WHERE %s', qualified_table, match_condition) INTO existing_record;

    FOR column_name, column_value IN SELECT * FROM jsonb_each(data) LOOP
        IF NOT (column_name = ANY(all_keys)) THEN
            IF existing_record IS NOT NULL AND existing_record ? column_name AND existing_record->>column_name IS DISTINCT FROM column_value#>>'{}' THEN
                needs_update := true;
            END IF;

            IF update_clause != '' THEN
                update_clause := update_clause || ', ';
            END IF;
            update_clause := update_clause || format('%I = %s', column_name, 
                CASE 
                    WHEN jsonb_typeof(column_value) = 'null' THEN 'NULL'
                    ELSE format('%L', column_value#>>'{}')
                END);
        END IF;

        IF insert_columns != '' THEN
            insert_columns := insert_columns || ', ';
            insert_values := insert_values || ', ';
        END IF;
        insert_columns := insert_columns || format('%I', column_name);
        insert_values := insert_values || 
            CASE 
                WHEN jsonb_typeof(column_value) = 'null' THEN 'NULL'
                ELSE format('%L', column_value#>>'{}')
            END;
    END LOOP;

    IF existing_record IS NOT NULL THEN
        IF needs_update AND update_clause != '' THEN
            EXECUTE format('UPDATE %s SET %s WHERE %s', qualified_table, update_clause, match_condition);
            action_performed := 'updated';
        ELSE
            action_performed := 'retrieved';
        END IF;
    ELSE
        EXECUTE format('INSERT INTO %s (%s) VALUES (%s)', qualified_table, insert_columns, insert_values);
        action_performed := 'created';
    END IF;

    EXECUTE format('SELECT to_jsonb(t.*) FROM %s t WHERE %s', qualified_table, match_condition) INTO existing_record;
    RETURN jsonb_set(existing_record, '{_action}', to_jsonb(action_performed));
END;
$$ LANGUAGE plpgsql;