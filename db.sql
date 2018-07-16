create table abstract_tasks
(
  id   INTEGER not null,
  name TEXT    not null
);

create unique index abstract_tasks_id_uindex
  on abstract_tasks (id);

create unique index abstract_tasks_name_uindex
  on abstract_tasks (name);

-- unexpected locus for key
;

create table tasks
(
  id               INTEGER not null,
  due_date         TEXT,
  name             TEXT    not null,
  priority         INTEGER default 0 not null,
  due_time         TEXT,
  status           INTEGER default 1 not null,
  weight           REAL    default 0 not null,
  abstract_task_id INTEGER default 1 not null
    constraint tasks_abstract_tasks_id_fk
    references abstract_tasks
);

create unique index tasks_id_uindex
  on tasks (id);

-- unexpected locus for key
;

CREATE TRIGGER "set_due_date"
  AFTER
  INSERT
  ON tasks
  FOR EACH ROW
  WHEN (new.due_date is null)
BEGIN
  UPDATE tasks
  SET due_date = date('now')
  WHERE id = new.id;
END;
