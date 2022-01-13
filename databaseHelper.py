import mysql.connector
import time
from datetime import datetime


class DB():
    def __init__(self,HOST, USERNAME, PASSWORD, PORT, DATABASE):
        self.HOST=HOST
        self.USERNAME=USERNAME
        self.PASSWORD=PASSWORD
        self.PORT=PORT
        self.DATABASE=DATABASE
        self.scoreboard_size=20
        self.db = self.createConnection()
        self.initDb()
    def createConnection(self):
        db = mysql.connector.connect(
            host=self.HOST,
            user=self.USERNAME,
            passwd=self.PASSWORD,
            database=self.DATABASE,
            port=self.PORT
        )
        self.cursor = db.cursor(dictionary=True)
        self.cursor.execute('SET NAMES utf8mb4')
        self.cursor.execute("SET CHARACTER SET utf8mb4")
        self.cursor.execute("SET character_set_connection=utf8mb4")
        self.cursor.execute("SET SQL_MODE='ALLOW_INVALID_DATES'")
        return db
    def check_cursor(self):
        try:
            self.db.ping(reconnect=True, attempts=3, delay=5)
        except mysql.connector.Error as err:
            # reconnect your cursor as you did in __init__ or wherever
            self.db = createConnection()
        self.cursor = self.db.cursor(dictionary=True)

    def escape(self,text):
        self.check_cursor()
        return self.cursor._connection.converter.escape(text)
    def initDb(self):
        self.check_cursor()
        # `users` ADD `discord_id` INT NULL DEFAULT NULL AFTER `latest_date`;

        sql=f"""CREATE TABLE IF NOT EXISTS `users` (`id` INT NOT NULL AUTO_INCREMENT,`solved_challenge_ids` VARCHAR(200) NULL,`total_points` INT NULL,`latest_date` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, `discord_id` VARCHAR(50) NULL DEFAULT NULL, PRIMARY KEY (`id`));"""
        self.cursor.execute(sql)
        self.db.commit()
        sql=f"""CREATE TABLE IF NOT EXISTS `challenges` (`id` INT NOT NULL AUTO_INCREMENT,`name` VARCHAR(70) NULL,`flag` VARCHAR(70) NULL,`points` INT NULL,PRIMARY KEY (`id`));"""
        self.cursor.execute(sql)
        self.db.commit()
    def getScoreboard(self):
        self.check_cursor()
        self.cursor.execute(f"SELECT *  FROM `users` ORDER BY `total_points` DESC ,`latest_date` ASC LIMIT {self.scoreboard_size}")
        res = self.cursor.fetchall()
        if res:
            length=len(res)
        else:
            length=0
        return res, length, self.scoreboard_size
    def getChallenges(self):
        self.check_cursor()
        self.cursor.execute(f"SELECT *  FROM `challenges`")
        res = self.cursor.fetchall()
        return res
    def getChallenge(self,challenge_name):
        self.check_cursor()
        self.cursor.execute(f"SELECT *  FROM `challenges` WHERE `name`='{challenge_name}'")
        res = self.cursor.fetchone()
        return res
    def deleteChallenge(self,challenge_name):
        self.check_cursor()
        self.cursor.execute(f"""DELETE FROM `challenges` WHERE (`id` = "{self.getChallenge(challenge_name)['id']}");""")
        self.db.commit()
    def getChallengewithID(self,ID):
        self.check_cursor()
        self.cursor.execute(f"SELECT *  FROM `challenges` WHERE `id`='{ID}'")
        res = self.cursor.fetchone()
        return res
    def addChallenge(self,name,flag,points):
        self.check_cursor()
        self.cursor.execute(f"""INSERT INTO `challenges` (`name`,`flag`, `points`) VALUES ('{name}','{flag}', '{points}');""")
        self.db.commit()
    def updateSolvedChallenge(self,discord_id,challenge_id):
        self.check_cursor()
        self.cursor.execute(f"SELECT *  FROM `challenges` WHERE `id`='{challenge_id}'")
        challenge = self.cursor.fetchone()
        user = self.getUser(discord_id)
        sql=f"""UPDATE `users` SET  `total_points` = `total_points`+"{challenge['points']}",
                        `solved_challenge_ids`=CONCAT(`solved_challenge_ids`,"{challenge_id},")
                        WHERE `id` = {user['id']}"""
        self.cursor.execute(sql)
        self.db.commit()
    def getUsers(self):
        self.check_cursor()
        self.cursor.execute(f"SELECT *  FROM `users`")
        res = self.cursor.fetchall()
        return res
    def addUser(self,discord_id):
        self.check_cursor()
        self.cursor.execute(f"""INSERT INTO `users` (`solved_challenge_ids`, `total_points`,`discord_id`) VALUES ('', '0','{discord_id}');""")
        self.db.commit()
    def deleteUser(self, discord_id):
        self.check_cursor()
        self.cursor.execute(f"""DELETE FROM `users` WHERE (`discord_id` = "{discord_id}");""")
        self.db.commit()
    def getUser(self,discord_id):
        self.check_cursor()
        self.cursor.execute(f"SELECT *  FROM `users` WHERE `discord_id`='{discord_id}'")
        res = self.cursor.fetchone()
        if not res:
            self.addUser(discord_id)
            res = self.getUser(discord_id)
        return res
    def getChallengeNames(self,discord_id,solved):
        self.check_cursor()
        user=self.getUser(discord_id)
        solved_challenge_ids = user['solved_challenge_ids'][:-1]
        if solved:
            if solved_challenge_ids=='':
                return ['Yok']
            self.cursor.execute(f"SELECT name FROM challenges WHERE id IN ({solved_challenge_ids})")
        else:
            if (solved_challenge_ids.count(',')+1)==len(self.getChallenges()):
                return ['Yok']
            if solved_challenge_ids=='':
                solved_challenge_ids='0'
            self.cursor.execute(f"SELECT name FROM challenges WHERE id NOT IN ({solved_challenge_ids})")
        return [i['name'] for i in self.cursor.fetchall()]
    def isCorrectFlag(self, flag, discord_id):
        self.check_cursor()
        challenges=self.getChallenges()
        for challenge in challenges:
            if flag==challenge["flag"]:
                solved_challenges=self.getChallengeNames(discord_id,solved=True)
                if challenge["name"] not in solved_challenges:
                    return ("CorrectFlag",challenge)
                else:
                    return ("AlreadySolved",challenge["name"])
        return ("NotCorrect","BOS")
