# Installing

```bash
sudo ln -s `pwd`/aide /usr/bin/aide
```

Create a minimal config file:

```bash
vim ~/.aide.conf

{
  "db_path": "/var/lib/aide/tasks.db", # could be any path
}
```

## Setting up a DB

```bash
sudo mkdir /var/lib/task/
sudo chown USER /var/lib/task/

sqlite3 /var/lib/task/tasks.db
```

# Useful aliases

```bash
alias tl="aide list -t"
alias tla="aide list -o"
alias ta="aide add"
alias cl="aide close"
```



