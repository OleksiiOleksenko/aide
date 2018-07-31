import sqlite3
import logging


def train(args, db, cursor: sqlite3.Cursor):
    if args.list:
        cursor.execute("SELECT id, xp, gold_reward, name FROM trainers")
        trainers = cursor.fetchall()
        print("ID : XP | G: | Name\n---------------------")
        for t in trainers:
            print("{:<3}: {:<2} | {:<2} | {}".format(t[0], t[1], t[2], t[3]))
        return

    if args.claim:
        cursor.execute("SELECT name, price FROM awards WHERE id = ?", (args.claim,))
        award = cursor.fetchone()
        logging.info("{} costed you {} gold".format(award[0], award[1]))

        cursor.execute("UPDATE character SET gold = gold - ? WHERE id = 1", (award[1],))
        db.commit()

        cursor.execute("SELECT gold FROM character WHERE id = 1")
        logging.info("Now you have " + str(cursor.fetchone()[0]) + " gold")

        return

    cursor.execute("SELECT name, xp, gold_reward, trained_skill FROM trainers WHERE id = ?", (args.id,))
    trainer = cursor.fetchone()
    if not trainer:
        logging.error("Not such trainer!")
        return

    logging.info("Training " + trainer[0])

    # level up, if necessary
    cursor.execute("SELECT xp, level, xp_for_next_level FROM character WHERE id = 1")
    character = cursor.fetchone()

    current_xp = character[0] + trainer[1]
    if current_xp > character[2]:
        logging.info("\n\n   Hey! You leveled up!!!\n")
        next_level = character[2] + 50 + character[1] * 5
        cursor.execute(
            "UPDATE character SET level = level + 1, xp_for_next_level = ? WHERE id = 1", (next_level,))

    # update xp and gold
    cursor.execute("UPDATE character SET xp = xp + ?, gold = gold + ? WHERE id = 1", (trainer[1], trainer[2]))

    # increase the skill
    cursor.execute("SELECT name, value, xp FROM skill WHERE id = ?", (trainer[3],))
    skill = cursor.fetchone()

    skill_xp = skill[2] + trainer[1]
    if skill_xp > 50:
        logging.info("Skill " + skill[0] + " increased to level " + str(skill[1] + 1))
        cursor.execute("UPDATE skill SET value = value + 1, xp = ? WHERE id = ?", (skill_xp - 50, trainer[3]))
    else:
        cursor.execute("UPDATE skill SET xp = ? WHERE id = ?", (skill_xp, trainer[3]))

    db.commit()


def award(args, db, cursor: sqlite3.Cursor):
    pass