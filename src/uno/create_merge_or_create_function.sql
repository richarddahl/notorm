CREATE OR REPLACE FUNCTION merge_or_insert(
    table_name text,
    data jsonb,
    primary_keys text[],
    unique_constraints text[]
) RETURNS jsonb AS $$
DECLARE
    match_condition text := '';
    update_clause text := '';
    insert_columns text := '';
    insert_values text := '';
    all_keys text[];
    existing_record jsonb;
    action_performed text;
    needs_update boolean := false;
BEGIN
    -- Validate inputs
    IF table_name IS NULL OR data IS NULL THEN
        RAISE EXCEPTION 'Invalid parameters: table_name and data must be provided';
    END IF;

    -- Determine matching keys
    IF array_length(primary_keys, 1) > 0 AND (SELECT bool_and(data ? key) FROM unnest(primary_keys) AS key) THEN
        all_keys := primary_keys;
    ELSIF array_length(unique_constraints, 1) > 0 AND (SELECT bool_and(data ? key) FROM unnest(unique_constraints) AS key) THEN
        all_keys := unique_constraints;
    ELSE
        RAISE EXCEPTION 'Neither primary keys nor unique constraints are available in the data';
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

    -- Check for existing record
    EXECUTE format('SELECT to_jsonb(t.*) FROM %I t WHERE %s', table_name, match_condition) INTO existing_record;

    -- Build update and insert clauses
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

    -- Determine action
    IF existing_record IS NOT NULL THEN
        IF needs_update THEN
            EXECUTE format('UPDATE %I SET %s WHERE %s', table_name, update_clause, match_condition);
            action_performed := 'updated';
        ELSE
            action_performed := 'retrieved';
        END IF;
    ELSE
        EXECUTE format('INSERT INTO %I (%s) VALUES (%s)', table_name, insert_columns, insert_values);
        action_performed := 'created';
    END IF;

    -- Return the final record with action
    EXECUTE format('SELECT to_jsonb(t.*) FROM %I t WHERE %s', table_name, match_condition) INTO existing_record;
    RETURN jsonb_set(existing_record, '{_action}', to_jsonb(action_performed));
END;
$$ LANGUAGE plpgsql;
