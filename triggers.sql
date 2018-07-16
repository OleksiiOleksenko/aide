DROP TRIGGER "main"."set_due_date";


CREATE TRIGGER "set_due_date"
   AFTER
   INSERT
   ON tasks
  FOR EACH ROW WHEN (new.due_date is null)
BEGIN
    UPDATE tasks SET due_date=date('now') WHERE id = new.id;
END;


CREATE TRIGGER "repeat_task"
   AFTER
   UPDATE
   ON tasks
  FOR EACH ROW WHEN (old.status = 1 AND new.status = 0 AND old.repeat_period is not null)
BEGIN
    INSERT INTO tasks(name, priority, due_time, weight, repeat_period, due_date)
    VALUES (old.name, old.priority, old.due_time, old.weight, old.repeat_period, date(old.due_date,old.repeat_period));
END;
