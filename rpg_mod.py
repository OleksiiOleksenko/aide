import sqlite3


def add_quest(db, cursor: sqlite3.Cursor, name: str, xp: int, gold_reward: int, trained_skill: int):
    cursor.execute("INSERT INTO quests(name, xp, willingness, trained_skill) VALUES (?, ?, ?, ?)",
                   (name, xp, gold_reward, trained_skill))
    db.commit()


def get_quests(cursor: sqlite3.Cursor):
    cursor.execute("SELECT id, xp, willingness, time, name FROM quests")
    quests = cursor.fetchall()
    return [{
        "id": q[0],
        "xp": q[1],
        "will": q[2],
        "time": q[3],
        "name": q[4]
    } for q in quests]


def close_quest(db, cursor: sqlite3.Cursor, id_: str):
    cursor.execute("SELECT name, xp, willingness, trained_skill, time FROM quests WHERE id = ?", (id_,))
    quest = cursor.fetchone()
    if not quest:
        return

    # level up, if necessary
    cursor.execute("SELECT xp, level, xp_for_next_level FROM character WHERE id = 1")
    character = cursor.fetchone()

    current_xp = character[0] + quest[1]
    levelup = False
    if current_xp > character[2]:
        levelup = True
        next_level = character[2] + 50 + character[1] * 5
        cursor.execute(
            "UPDATE character SET level = level + 1, xp_for_next_level = ? WHERE id = 1", (next_level,))

    # update xp and gold
    will = int(quest[2])
    time = int(quest[4])
    gold = ((10 - will) // 2) * time
    if levelup:
        gold += 100
    cursor.execute("UPDATE character SET xp = xp + ?, gold = gold + ? WHERE id = 1", (quest[1], gold))

    # increase the skill
    cursor.execute("SELECT name, value, xp FROM skills WHERE id = ?", (quest[3],))
    skill = cursor.fetchone()

    skill_xp = skill[2] + quest[1]
    skill_increased = False
    if skill_xp > 50:
        skill_increased = True
        cursor.execute("UPDATE skills SET value = value + 1, xp = ? WHERE id = ?", (skill_xp - 50, quest[3]))
    else:
        cursor.execute("UPDATE skills SET xp = ? WHERE id = ?", (skill_xp, quest[3]))

    db.commit()
    return quest[0], levelup, skill_increased, skill[0], str(skill[1] + 1)


def add_award(db, cursor: sqlite3.Cursor, name: str, price: int):
    cursor.execute("INSERT INTO awards(name, price) VALUES (?, ?)",
                   (name, price))
    db.commit()


def get_awards(cursor: sqlite3.Cursor):
    cursor.execute("SELECT id, name, price FROM awards")
    awards = cursor.fetchall()
    return [{
        "id": a[0],
        "name": a[1],
        "price": a[2],
    } for a in awards]


def claim_award(db, cursor: sqlite3.Cursor, id_: str):
    cursor.execute("SELECT name, price FROM awards WHERE id = ?", (id_,))
    award = cursor.fetchone()

    cursor.execute("UPDATE character SET gold = gold - ? WHERE id = 1", (award[1],))
    db.commit()

    cursor.execute("SELECT gold FROM character WHERE id = 1")
    gold = cursor.fetchone()

    return award[0], award[1], str(gold[0])


def get_character_stats(cursor: sqlite3.Cursor):
    cursor.execute("SELECT level, gold, xp, xp_for_next_level FROM character WHERE id = 1")
    character = cursor.fetchone()
    return {
        "level": character[0],
        "gold": character[1],
        "xp": character[2],
        "xp_for_next_level": character[3]
    }


def get_skills(cursor: sqlite3.Cursor):
    cursor.execute("SELECT id, name, value, xp FROM skills")
    skills = cursor.fetchall()
    return [{
        "id": s[0],
        "name": s[1],
        "value": s[2],
        "xp": s[3]
    } for s in skills]
