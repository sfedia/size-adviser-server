#!/usr/bin/python3

from random import randint
from typing import Dict, Iterable, List, Union
import sqlite3


class FittingSession:
    def __init__(self, user_id=None, fitting_id=None):
        self.user_id = user_id
        self.fitting_id = fitting_id
        if not user_id and not fitting_id:
            raise ValueError
        if user_id and not fitting_id:
            self.fitting_id = str(randint(10**(8-1), (10**8)-1))
        self.db = sqlite3.connect("../DATABASES/personal.sqlite3")
        self.c = self.db.cursor()

    @staticmethod
    def make_photo_id():
        return str(randint(10**(8-1), (10**8)-1))

    def fs_media_adding(self, binary, extension, folder="media"):
        _id = self.make_photo_id()
        self.db_media_adding("%s.%s" % (_id, extension))
        fl = open(folder + "/%s.%s" % (_id, extension), "wb")
        fl.write(binary)
        fl.close()

    def number_of_tries(self):
        return self.c.execute("SELECT COUNT(*) FROM fitting WHERE user_id='%s'" % (self.user_id)).fetchone()[0]

    def try_with_size(self, brand, size, fit_value, date, geo, rewrite=True):
        if rewrite:
            self.c.execute(f"DELETE FROM fitting WHERE brand='{brand}' AND size='{size}' AND user_id='{self.user_id}'")
        self.c.execute("INSERT INTO fitting VALUES (?,?,?,?,?,?,?)", (
            self.user_id, self.fitting_id, brand, size, fit_value, date, geo
        ))
        self.db.commit()

    def get_user_best_fits(self):
        data = self.c.execute(
            f"SELECT brand, size, fit_value FROM fitting WHERE user_id='{self.user_id}'").fetchall()
        result = {}
        for (brand, size, fit_value) in data:
            fit_value = int(fit_value)
            if brand not in result or abs(fit_value-3) < abs(result[brand][1]-3):
                result[brand] = [size, fit_value]
        return result

    def get_user_collection(self) -> Dict[str, List[Union[str, None]]]:
        data = self.c.execute(
            f"""SELECT brand, size, fit_value, fitting_id, date, photo_id FROM (
                    SELECT brand, size, fit_value, fitting.fitting_id, brand_photos.photo_id, fitting.user_id, date
                    FROM fitting LEFT OUTER JOIN brand_photos ON fitting.fitting_id = brand_photos.fitting_id
                ) WHERE user_id='{self.user_id}' GROUP BY fitting_id""").fetchall()
        return [{brand: [size, int(fit_value), fitting_id, date, photo_id]} for (brand, size, fit_value, fitting_id, date, photo_id) in data]

    def remove_fitting_data(self):
        self.c.execute(f"DELETE FROM fitting WHERE fitting_id='{self.fitting_id}'")
        self.db.commit()
        return True

    def remove_photo(self, photo_id):
        self.c.execute(f"DELETE FROM brand_photos WHERE photo_id='{photo_id}' AND fitting_id='{self.fitting_id}'")
        self.db.commit()
        return True

    def remove_photo_by_index(self, photo_index=-1):
        self.c.execute(f"DELETE FROM brand_photos WHERE fitting_id='{self.fitting_id}' LIMIT 1 OFFSET {photo_index}")
        self.db.commit()
        return True

    def attribute_tried(self, brand_list, attr_func):
        sql_list = ",".join(["'%s'" % b for b in brand_list])
        tried = [row[0] for row in self.c.execute("SELECT DISTINCT brand FROM fitting WHERE brand IN (%s) AND "
                       "user_id='%s'" % (sql_list, self.user_id))]
        return [attr_func(brand, brand in tried) for brand in brand_list]

    def db_media_adding(self, photo_id, extension=""):
        self.c.execute("INSERT INTO brand_photos VALUES (?,?)", (self.fitting_id, photo_id + extension))
        self.db.commit()

    def get_recorded_brands(self) -> Iterable[str]:
        return map(lambda x: x[0], self.c.execute("SELECT DISTINCT brand FROM fitting").fetchall())

    def wo_table_fitting(self, brand: str) -> Dict[str, str]:
        query = f"SELECT size FROM fitting WHERE user_id='{self.user_id}' AND brand='{brand}'"
        result: str = self.c.execute(query).fetchone()[0]
        size, standard = result.split()
        return {standard: size}

    def stop(self):
        self.db.close()


def save_user_props(user_id, gender):
    db = sqlite3.connect("../DATABASES/personal.sqlite3")
    c = db.cursor()
    c.execute("INSERT INTO user_props VALUES (?,?)", (user_id, gender))
    db.commit()
    db.close()
