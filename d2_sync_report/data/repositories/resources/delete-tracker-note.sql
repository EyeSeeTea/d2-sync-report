-- Given a constraint name and a UID, delete the row comment
-- Typically used to delete trackedEntity/enrollment/event comments.

-- Usage:
--   $ docker exec -i CONTAINER psql -U dhis dhis2 \
--       --set=constraint_name="'your_constraint'" \
--       --set=uid_to_delete="'your_uid'" \
--       --set=delete='yes' \
--       -f delete-tracker-note.sql

-- Get table and column info from constraint
WITH constraint_info AS (
    SELECT
        conrelid::regclass::text AS table_name
    FROM
        pg_constraint c
        JOIN unnest(c.conkey) AS colnum ON true
        JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = colnum
    WHERE
        c.conname = :constraint_name
),
-- Dynamically construct the SQL query
query_parts AS (
    SELECT
        CASE
            WHEN :'delete' = 'yes' THEN

----


                format(
                    $$WITH row_data AS (
                        SELECT * FROM %I WHERE uid = %L
                    )
                    SELECT 'Deleting row:' AS notice, row_to_json(row_data) FROM row_data;
                    DELETE FROM %I WHERE uid = %L;$$,
                    table_name, :uid_to_delete,
                    table_name, :uid_to_delete
                )







----

            ELSE
                format(
                    $$WITH row_data AS (
                        SELECT * FROM %I WHERE uid = %L
                    )
                    SELECT 'Matched row (dry run, not deleted):' AS notice, row_to_json(row_data) FROM row_data;$$,
                    table_name, :uid_to_delete
                )
        END AS full_query
    FROM constraint_info
)
-- Execute the constructed SQL
SELECT full_query FROM query_parts \gexec
