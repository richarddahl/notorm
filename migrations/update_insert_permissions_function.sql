CREATE OR REPLACE FUNCTION uno.insert_permissions()
RETURNS trigger AS $$
BEGIN
    -- Fully qualify the permission table with the uno schema
    INSERT INTO uno.permission(meta_type_id, operation)
    VALUES (NEW.id, 'SELECT'::uno.sqloperation);
    RETURN NEW;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Error in insert_permissions: %', SQLERRM;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;