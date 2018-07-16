# Installing

```bash
sudo ln -s `pwd`/aide /usr/bin/aide
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
alias ta="aide add"
alias cl="aide close 99 && task list"
```



