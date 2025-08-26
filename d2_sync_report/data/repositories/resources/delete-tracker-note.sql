-- Given a note/comment UID, delete the relationships to enrollments/events in the database.
--
-- Tracker notes (comments) are read-only and cannot be deleted thought the API. We will
-- delete the relationship but not the comment itself, so we can recover it if necessary
--
-- dhis2=# SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND
--           table_type = 'BASE -- TABLE' AND table_name LIKE '%comment%'
--           and table_name not like '%interpretation%';
--
--           table_name
-- ------------------------------
-- programinstancecomments       <- intermediate table enrollment/comment
-- programstageinstancecomments  <- intermediate table event/comment
-- trackedentitycomment          <- the comment itself
--
-- Usage:
--
--   $ docker exec -i CONTAINER psql -U dhis dhis2 \
--       --set=note_uid="note_uid" \
--       --set=dryrun=1 \ <- optional, default is no dry run
--       -f delete-tracker-note.sql

BEGIN;
    DELETE FROM programstageinstancecomments
        WHERE trackedentitycommentid IN (
            SELECT trackedentitycommentid
            FROM trackedentitycomment
            WHERE uid = :'note_uid'
        );

    DELETE FROM programinstancecomments
        WHERE trackedentitycommentid IN (
            SELECT trackedentitycommentid
            FROM trackedentitycomment
            WHERE uid = :'note_uid'
        );
-- Conditionally ROLLBACK or COMMIT
\if :{?dryrun}
  \if :dryrun
    ROLLBACK;
  \else
    COMMIT;
  \endif
\else
  COMMIT;
\endif
