-- DROP TRIGGER "main"."set_due_date";
DROP TRIGGER "main"."repeat_task";
DROP TRIGGER "main"."repeat_task_workdays";


-- CREATE TRIGGER "set_due_date"
--    AFTER
--    INSERT
--    ON tasks
--   FOR EACH ROW WHEN (new.due_date is null)
-- BEGIN
--     UPDATE tasks SET due_date=date('now') WHERE id = new.id;
-- END;

CREATE TRIGGER "repeat_task"
    AFTER UPDATE
    ON tasks
    FOR EACH ROW WHEN (old.status = 1 AND new.status = 0 AND old.repeat_period is not null AND old.repeat_period != 'workdays' AND old.repeat_period != '')
BEGIN
    INSERT INTO tasks(name, priority, due_time, weight, repeat_period, due_date, quest)
    VALUES (old.name, old.priority, old.due_time, old.weight, old.repeat_period, date(old.due_date,old.repeat_period), old.quest);
END;


CREATE TRIGGER "repeat_task_workdays"
    AFTER UPDATE
    ON tasks
    FOR EACH ROW WHEN (old.status = 1 AND new.status = 0 AND old.repeat_period is not null AND old.repeat_period == 'workdays' AND old.repeat_period != '')
BEGIN
    INSERT INTO tasks(name, priority, due_time, weight, repeat_period, quest, due_date)
    VALUES (old.name, old.priority, old.due_time, old.weight, old.repeat_period, old.quest,
            CASE strftime("%w", date(old.due_date))
                WHEN 5 THEN date(old.due_date,'weekday 1')
                ELSE date(old.due_date,'+1 days')
            END
           );
END;

