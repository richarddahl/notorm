CREATE OR REPLACE FUNCTION merge_or_insert(
    table_name text, 
    data jsonb, 
    pk_fields text[], 
    uq_field_sets jsonb[]
) RETURNS TABLE (result jsonb) AS $$
DECLARE
    columns text;
    values text;
    match_conditions text;
    update_set text;
    sql text;
    pk_match_conditions text;
    uq_match_conditions text;
BEGIN
    --RAISE EXCEPTION 'data: %', data;
    -- Extract column names and values from the JSONB data
    SELECT string_agg(key, ', ') INTO columns
    FROM jsonb_object_keys(data);

    SELECT string_agg(format('%%L AS %I', value, key), ', ') INTO values
    FROM jsonb_each_text(data);

    -- Generate the update set clause
    SELECT string_agg(format('%I = EXCLUDED.%I', key, key), ', ') INTO update_set
    FROM jsonb_object_keys(data);

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
        FROM unnest(uq_field_sets) AS uq_set, unnest(uq_set::TEXT[]) AS field;
        FROM unnest(uq_field_sets) AS uq_set, unnest(uq_set::TEXT[]) AS field;

        IF match_conditions <> '' THEN
            match_conditions := match_conditions || ' OR ' || uq_match_conditions;
        ELSE
            match_conditions := uq_match_conditions;
        END IF;
    END IF;

    -- Construct the MERGE statement with a RETURNING clause
    sql := format(
        'WITH source AS (
            SELECT %s
        )
        MERGE INTO %I AS target
        USING source
        ON %s
        WHEN MATCHED THEN
            UPDATE SET %s
            RETURNING target.*
        WHEN NOT MATCHED THEN
            INSERT (%s) VALUES (%s)
            RETURNING target.*',
        values, table_name, match_conditions, update_set, columns, columns
    );

    -- Debugging: Print the generated SQL
    RAISE NOTICE 'Generated SQL: %', sql;

    -- Execute the MERGE statement and return the results
    RETURN QUERY EXECUTE sql;
END;
$$ LANGUAGE plpgsql;
