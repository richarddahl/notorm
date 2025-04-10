CREATE OR REPLACE FUNCTION merge_record(
    table_name text,
    data jsonb
) RETURNS jsonb AS $$
DECLARE
    match_condition text := '';
    update_set_clause text := '';
    insert_columns text := '';
    insert_values text := '';
    merge_query text;
    primary_keys text[] := '{}';
    all_keys text[];
    result_record jsonb;
    existing_record jsonb;
    action_performed text;
    column_name text;
    column_value jsonb;
    schema_name text := 'public';
    table_parts text[];
    qualified_table text;
    debug_info jsonb;
    data_keys text[];
    source_clause text := '';
    record_exists boolean := false;
    needs_update boolean := false;
BEGIN
    /*
        Function: merge_record

        TODO:
        PG16's MERGE statement does not support RETURNING, so we need to do a
        SELECT after the MERGE to get the final state of the record.
        Once uno is updated to PG17 (assuming apache age gets updated to PG 17), 
        we can use the RETURNING clause in the MERGE statement.

        Description:
        This function performs a "merge" or "upsert" operation on a specified table. 
        It attempts to insert a new record into the table or update an existing record 
        if a match is found based on primary keys or unique constraints. If no match 
        is found, a new record is inserted. If a match is found but the data differs, 
        the record is updated. If a match is found and no changes are needed, the 
        existing record is returned.

        Parameters:
        - table_name (text): The name of the target table. It can include the schema 
        (e.g., 'schema_name.table_name') or just the table name. If no schema is 
        provided, the default schema 'public' is assumed.
        - data (jsonb): A JSONB object containing the data to be inserted or updated. 
        The keys in the JSONB object represent column names, and the values represent 
        the corresponding values for those columns.

        Returns:
        - jsonb: A JSONB object representing the final state of the record after the 
        operation. An additional key `_action` is included to indicate whether the 
        record was 'inserted', 'updated', or 'selected'.

        Behavior:
        1. Validates the input parameters to ensure both `table_name` and `data` are provided.
        2. Determines the schema and table name from the `table_name` parameter.
        3. Identifies the keys to use for matching records:
        - Primary keys are preferred if all primary key columns are present in the data.
        - Single-column unique constraints are used if primary keys are not usable.
        - Multi-column unique constraints are used as a last resort.
        4. If no usable keys are found, an exception is raised with debug information.
        5. Checks if a record exists in the table based on the identified keys.
        6. If a record exists, determines if any non-key columns need to be updated.
        7. Constructs and executes a SQL `MERGE` statement to perform the insert or update:
        - If a match is found and changes are needed, the record is updated.
        - If no match is found, a new record is inserted.
        8. Retrieves the final state of the record after the operation.
        9. Adds an `_action` key to the result to indicate the performed action.

        Debugging:
        - If no primary keys or unique constraints are found, the function raises an 
        exception with debug information, including the table name, schema, data keys, 
        primary keys, and selected keys.

        Notes:
        - The function assumes that the table has at least one primary key or unique 
        constraint to identify records.
        - The function uses PostgreSQL's `MERGE` statement for the upsert operation.
        - The function handles NULL values in the JSONB data appropriately.

        Example Usage:
        SELECT merge_record('my_table', '{"id": 1, "name": "John", "age": 30}'::jsonb);
    */

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

    -- APPROACH 1: Try to use primary key if all columns are in the data
    SELECT array_agg(a.attname::text) INTO primary_keys
    FROM pg_index i
    JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
    WHERE i.indrelid = (schema_name || '.' || table_name)::regclass
    AND i.indisprimary;
    
    IF primary_keys IS NOT NULL AND array_length(primary_keys, 1) > 0 THEN
        IF (SELECT bool_and(data ? key) FROM unnest(primary_keys) AS key) THEN
            all_keys := primary_keys;
        END IF;
    END IF;

    -- APPROACH 2: If primary key not usable, try each single-column unique constraint
    IF all_keys IS NULL THEN
        -- Get all single-column unique constraints
        SELECT a.attname INTO column_name
        FROM pg_index i
        JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
        WHERE i.indrelid = (schema_name || '.' || table_name)::regclass
        AND i.indisunique AND NOT i.indisprimary
        AND array_length(i.indkey, 1) = 1  -- Single-column unique constraints
        AND data ? a.attname  -- Column exists in the data
        LIMIT 1;
        
        IF column_name IS NOT NULL THEN
            all_keys := ARRAY[column_name];
        END IF;
    END IF;

    -- APPROACH 3: If still no keys, try multi-column unique constraints
    IF all_keys IS NULL THEN
        WITH unique_constraints AS (
            SELECT i.indexrelid, array_agg(a.attname ORDER BY array_position(i.indkey, a.attnum)) as columns
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = (schema_name || '.' || table_name)::regclass
            AND i.indisunique AND NOT i.indisprimary
            AND array_length(i.indkey, 1) > 1  -- Multi-column unique constraints
            GROUP BY i.indexrelid
        )
        SELECT columns INTO all_keys
        FROM unique_constraints
        WHERE (SELECT bool_and(data ? col) FROM unnest(columns) AS col)
        LIMIT 1;
    END IF;

    -- Create debug info
    debug_info := jsonb_build_object(
        'table', table_name,
        'schema', schema_name,
        'data_keys', to_jsonb(data_keys),
        'primary_keys', to_jsonb(primary_keys),
        'selected_keys', to_jsonb(all_keys)
    );

    -- Raise exception if no usable keys found
    IF all_keys IS NULL OR array_length(all_keys, 1) = 0 THEN
        RAISE EXCEPTION 'No primary keys or unique constraints found in the data. Ensure that the data includes at least one primary key or unique constraint. Debug: %', debug_info;
    END IF;

    -- First check if the record exists and get its current values
    EXECUTE format('
        SELECT EXISTS(
            SELECT 1 FROM %s
            WHERE %s
        ),
        (SELECT to_jsonb(t.*) FROM %s t WHERE %s)
    ',
    qualified_table,
    array_to_string(
        array(
            SELECT format('%I = %L', key, data->>key)
            FROM unnest(all_keys) AS key
        ),
        ' AND '
    ),
    qualified_table,
    array_to_string(
        array(
            SELECT format('%I = %L', key, data->>key)
            FROM unnest(all_keys) AS key
        ),
        ' AND '
    )
    ) INTO record_exists, existing_record;

    -- Check if any non-key columns need to be updated
    IF record_exists THEN
        needs_update := false;
        FOR column_name, column_value IN SELECT * FROM jsonb_each(data) LOOP
            IF NOT (column_name = ANY(all_keys)) AND 
               (NOT existing_record ? column_name OR 
                existing_record->>column_name IS DISTINCT FROM column_value#>>'{}') THEN
                needs_update := true;
                EXIT;
            END IF;
        END LOOP;
    END IF;

    -- Build match condition for the MERGE statement
    FOREACH column_name IN ARRAY all_keys LOOP
        IF match_condition != '' THEN
            match_condition := match_condition || ' AND ';
        END IF;
        match_condition := match_condition || format('target.%I = source.%I', column_name, column_name);
    END LOOP;

    -- Build source CTE clause
    FOR column_name, column_value IN SELECT * FROM jsonb_each(data) LOOP
        IF source_clause != '' THEN
            source_clause := source_clause || ', ';
        END IF;
        source_clause := source_clause || format(
            '%s AS %I',
            CASE 
                WHEN jsonb_typeof(column_value) = 'null' THEN 'NULL'
                ELSE format('%L', column_value#>>'{}')
            END,
            column_name
        );
        
        -- Add to insert columns and update clause
        IF insert_columns != '' THEN
            insert_columns := insert_columns || ', ';
            insert_values := insert_values || ', ';
        END IF;
        insert_columns := insert_columns || quote_ident(column_name);
        insert_values := insert_values || format('source.%I', column_name);
        
        -- Add to update clause if not a key column
        IF NOT (column_name = ANY(all_keys)) THEN
            IF update_set_clause != '' THEN
                update_set_clause := update_set_clause || ', ';
            END IF;
            update_set_clause := update_set_clause || format('%I = source.%I', column_name, column_name);
        END IF;
    END LOOP;

    -- Only perform the operation if we need to create or update
    IF NOT record_exists OR needs_update THEN
        -- Construct the MERGE statement without RETURNING
        merge_query := format('
            WITH source AS (
                SELECT %s
            )
            MERGE INTO %s AS target
            USING source
            ON %s
            WHEN MATCHED %s THEN
                UPDATE SET %s
            WHEN NOT MATCHED THEN
                INSERT (%s)
                VALUES (%s);
            --RETURNING merge_action(), target.*
            -- TODO: No RETURNING clause in PG16,
            -- so select after the MERGE for now
        ',
        source_clause,
        qualified_table,
        match_condition,
        CASE WHEN needs_update THEN '' ELSE 'AND false' END,
        CASE WHEN update_set_clause = '' THEN 'id = id' ELSE update_set_clause END,
        insert_columns,
        insert_values
        );

        -- Execute the MERGE statement
        EXECUTE merge_query;
    END IF;
    
    -- Now get the final record
    EXECUTE format('
        SELECT to_jsonb(t.*)
        FROM %s t
        WHERE %s
    ',
    qualified_table,
    array_to_string(
        array(
            SELECT format('t.%I = %L', key, data->>key)
            FROM unnest(all_keys) AS key
        ),
        ' AND '
    )
    ) INTO result_record;

       -- Determine action performed
    IF NOT record_exists THEN
        action_performed := 'inserted';
    ELSIF needs_update THEN
        action_performed := 'updated';
    ELSE
        action_performed := 'selected';
    END IF;
    
    -- Add the action to the result
    result_record := jsonb_set(result_record, '{_action}', to_jsonb(action_performed));
    
    RETURN result_record;
END;
$$ LANGUAGE plpgsql; 