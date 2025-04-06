CREATE OR REPLACE FUNCTION merge_or_insert(
    table_name text, 
    data jsonb, 
    pk_fields text[], 
    uq_fields jsonb[]
) RETURNS TABLE (result jsonb) AS $$
DECLARE
    columns_array text[];
    values_array text[];
    update_set_array text[];
    pk_match_conditions_array text[];
    uq_match_conditions_array text[];
    columns text;
    values text;
    update_set text;
    sql text;
    match_conditions text;
    pk_match_conditions text;
    uq_match_conditions text;
BEGIN
    -- Extract column names and values from the JSONB data
    SELECT array_agg(key) INTO columns_array
    FROM jsonb_object_keys(data) AS key;

    SELECT array_agg(format('%%L', value)) INTO values_array
    FROM jsonb_each(data) AS key_value(key, value);

    columns := array_to_string(columns_array, ', ');
    values := array_to_string(
        ARRAY(
            SELECT format('%%L', value)
            FROM unnest(values_array) AS value
        ), ', '
    );

    -- Generate the update set clause
    SELECT array_agg(format('%I = EXCLUDED.%I', key, key)) INTO update_set_array
    FROM jsonb_object_keys(data) AS key;

    update_set := array_to_string(update_set_array, ', ');

    -- Construct match conditions for primary keys and unique fields
    SELECT array_agg(format('%I = EXCLUDED.%I', field, field)) INTO pk_match_conditions_array
    FROM unnest(pk_fields) AS field;

    pk_match_conditions := array_to_string(pk_match_conditions_array, ' AND ');

    pk_match_conditions := array_to_string(pk_match_conditions_array, ' AND ');

    IF array_length(uq_fields, 1) > 0 THEN
        -- Check if there are any unique fields to consider for conflict resolution
        IF array_length(uq_fields, 1) > 0 THEN
            -- Construct match conditions for unique fields
            SELECT array_agg(
                format('(%s)', array_to_string(
                    ARRAY(
                        SELECT format('%I = EXCLUDED.%I', field, field)
                        FROM unnest(uq_set) AS field
                    ), ' AND '
                ))
            ) INTO uq_match_conditions_array
            FROM unnest(uq_fields) AS uq_set;

            -- Combine unique field conditions with OR logic
            uq_match_conditions := array_to_string(uq_match_conditions_array, ' OR ');

            -- Combine primary key and unique field conditions
            match_conditions := format('(%s) OR (%s)', pk_match_conditions, uq_match_conditions);
        ELSE
            -- If no unique fields, use only primary key conditions
            match_conditions := pk_match_conditions;
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
