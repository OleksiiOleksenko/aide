-- we don't know how to generate schema main (class Schema) :(
create table abstract_tasks
(
	id INTEGER not null,
	name TEXT not null
)
;

create unique index abstract_tasks_id_uindex
	on abstract_tasks (id)
;

create unique index abstract_tasks_name_uindex
	on abstract_tasks (name)
;

-- unexpected locus for key
;

create table day_notes
(
	id INTEGER not null,
	date TEXT not null,
	text TEXT not null
)
;

create unique index day_notes_id_uindex
	on day_notes (id)
;

-- unexpected locus for key
;

create table tasks
(
	id INTEGER not null,
	due_date TEXT,
	name TEXT not null,
	priority INTEGER default 0 not null,
	due_time TEXT,
	status INTEGER default 1 not null,
	weight REAL default 0 not null,
	abstract_task_id INTEGER default 1 not null
		constraint tasks_abstract_tasks_id_fk
			references abstract_tasks,
	repeat_period TEXT
)
;

create unique index tasks_id_uindex
	on tasks (id)
;

-- unexpected locus for key
;

CREATE TRIGGER "repeat_task"
   AFTER
   UPDATE
   ON tasks
  FOR EACH ROW WHEN (old.status = 1 AND new.status = 0 AND old.repeat_period is not null)
BEGIN
    INSERT INTO tasks(name, priority, due_time, weight, repeat_period, due_date)
    VALUES (old.name, old.priority, old.due_time, old.weight, old.repeat_period, date(old.due_date,old.repeat_period));
END;

CREATE TRIGGER "set_due_date"
   AFTER
   INSERT
   ON tasks
  FOR EACH ROW WHEN (new.due_date is null)
BEGIN
    UPDATE tasks SET due_date=date('now') WHERE id = new.id;
END;

