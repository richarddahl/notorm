CREATE OR REPLACE FUNCTION merge_or_insert(
    table_name text, 
    data jsonb, 
    pk_fields text[], 
    uq_fields jsonb[]
) RETURNS TABLE (result jsonb) AS $$
DECLARE
    columns text;
    values text;
    update_set text;
    sql text;
    match_conditions text;
BEGIN
    -- Extract column names and values from the JSONB data
    SELECT string_agg(key, ', ') INTO columns
    FROM jsonb_object_keys(data) AS key;

    SELECT string_agg(format('%%L', value), ', ') INTO values
    FROM jsonb_each_text(data) AS key_value(key, value);

    -- Generate the update set clause
    SELECT string_agg(format('%I = EXCLUDED.%I', key, key), ', ') INTO update_set
    FROM jsonb_object_keys(data) AS key;

    -- Construct match conditions for primary keys and unique fields
    SELECT string_agg(format('%I = EXCLUDED.%I', field, field), ' AND ') INTO match_conditions
    FROM unnest(pk_fields) AS field;

    IF array_length(uq_fields, 1) > 0 THEN
        SELECT string_agg(
            format('(%s)', string_agg(format('%I = EXCLUDED.%I', field, field), ' AND ')),
            ' OR '
        ) INTO match_conditions
        FROM unnest(uq_fields) AS uq_set, unnest(uq_set) AS field;
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
