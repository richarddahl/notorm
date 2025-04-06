CREATE OR REPLACE FUNCTION merge_or_insert(
    table_name text, 
    data jsonb, 
    pk_fields text[], 
    uq_field_sets jsonb
) RETURNS TABLE (result jsonb) AS $$
DECLARE
    columns text;
    values text;
    match_conditions text;
    update_set text;
    sql text;
    pk_match_conditions text;
    uq_match_conditions text;
    columns_array text[];
    values_array text[];
BEGIN
    -- Extract column names and values from the JSONB data
    SELECT array_agg(key) INTO columns_array
    FROM jsonb_object_keys(data) AS key;

    SELECT array_agg(format('%%L AS %I', value, key)) INTO values_array
    FROM jsonb_each_text(data) AS key_value(key, value);

    columns := array_to_string(columns_array, ', ');
    values := array_to_string(values_array, ', ');

    -- Generate the update set clause
    SELECT string_agg(format('%I = EXCLUDED.%I', key, key), ', ') INTO update_set
    FROM jsonb_object_keys(data) AS key;

    -- Initialize match conditions
    match_conditions := '';

    -- Add primary key conditions
    IF array_length(pk_fields, 1) > 0 THEN
        SELECT string_agg(format('%I = EXCLUDED.%I', field, field), ' AND ') INTO pk_match_conditions
        FROM unnest(pk_fields) AS field;

        match_conditions := format('(%s)', pk_match_conditions);
    END IF;

    -- Add unique field sets conditions
    IF jsonb_array_length(uq_field_sets) > 0 THEN
        SELECT string_agg(
            format('(%s)', string_agg(format('%I = EXCLUDED.%I', field, field), ' AND ')),
            ' OR '
        ) INTO uq_match_conditions
        FROM jsonb_array_elements(uq_field_sets) AS uq_set, jsonb_array_elements_text(uq_set) AS field;

        IF match_conditions <> '' THEN
            match_conditions := match_conditions || ' OR ' || uq_match_conditions;
        ELSE
            match_conditions := uq_match_conditions;
        END IF;
    END IF;

    -- Construct the SQL statement with a RETURNING clause
    sql := format(
        'INSERT INTO %I (%s) VALUES (%s)
        ON CONFLICT (%s) DO UPDATE SET %s
        RETURNING to_jsonb(%I.*)',
        table_name, columns, values, match_conditions, update_set, table_name
    );

    -- Execute the SQL statement and return the results
    RETURN QUERY EXECUTE sql;
END;
$$ LANGUAGE plpgsql;
