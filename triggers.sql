DROP TRIGGER "main"."set_due_date";


CREATE TRIGGER "set_due_date"
   AFTER
   INSERT
   ON tasks
  FOR EACH ROW WHEN (new.due_date is null)
BEGIN
    UPDATE tasks SET due_date=date('now') WHERE id = new.id;
END;
