TABLES = {}
TABLES['user'] = (
    "CREATE TABLE `user` ("
    "   `id` INT NOT NULL AUTO_INCREMENT,"
    "   `username` VARCHAR(255) UNIQUE NOT NULL,"
    "   `password` VARCHAR(255) NOT NULL,"
    "   PRIMARY KEY(`id`)"
    ") ENGINE=InnoDB"
)
TABLES['record'] = (
    "CREATE TABLE `record` ("
    "   `id` INT NOT NULL AUTO_INCREMENT,"
    "   `user_id` INT NOT NULL,"
    "   `release_title` VARCHAR(255) NOT NULL,"
    "   `artist` VARCHAR(255) NOT NULL,"
    "   `discogs_uri` VARCHAR(255) NOT NULL,"
    "   `image_url` VARCHAR(255) NOT NULL,"
    "   PRIMARY KEY(`id`),"
    "   FOREIGN KEY(`user_id`) REFERENCES `user`(`id`)"
    ") ENGINE=InnoDB"
)
TABLES['friend'] = (
    "CREATE TABLE `friend` ("
    "   `id` INT NOT NULL AUTO_INCREMENT,"
    "   `user_id` INT NOT NULL,"
    "   `friend_id` INT NOT NULL,"
    "   PRIMARY KEY(`id`),"
    "   FOREIGN KEY(`user_id`) REFERENCES `user`(`id`),"
    "   FOREIGN KEY(`friend_id`) REFERENCES `user`(`id`)"
    ") ENGINE=InnoDB"
)