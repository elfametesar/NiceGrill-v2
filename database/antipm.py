#    This file is part of NiceGrill.

#    NiceGrill is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    NiceGrill is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with NiceGrill.  If not, see <https://www.gnu.org/licenses/>.

from database.mongo import Mongo

Mongo = Mongo["NiceGrill"]["AntiPM"]


def set_antipm(switch: bool):
    delete_data("AntiPM")
    return Mongo.insert_one({"AntiPM": switch})


def approve_user(user_id: int):
    disapprove_user(user_id)
    return Mongo.insert_one({"Approved": user_id})


def get_all_approved():
    return [pair.get("Approved") for pair in Mongo.find() if pair.get("Approved")]


def set_warning_limit(warning_count: int):
    delete_data("Warning Count")
    return Mongo.insert_one({"Warning Count": warning_count})


def set_notifications(switch: bool):
    delete_data("Notifications")
    return Mongo.insert_one({"Notifications": switch})


def set_superblock(switch: bool):
    delete_data("Superblocking")
    return Mongo.insert_one({"Superblocking": switch})


def is_antipm():
    if antipm_data := Mongo.find_one({"AntiPM": {"$exists": True}}):
        return antipm_data["AntiPM"]


def get_warning_limit():
    if warning_count_data := Mongo.find_one({"Warning Count": {"$exists": True}}):
        return warning_count_data["Warning Count"]


def is_superblock():
    if superblock_data := Mongo.find_one({"Superblocking": {"$exists": True}}):
        return superblock_data["Superblocking"]


def is_notifications():
    if notifications_data := Mongo.find_one({"Notifications": {"$exists": True}}):
        return notifications_data["Notifications"]


def is_approved(user_id: int):
    return Mongo.find_one({"Approved": user_id})


def delete_data(data_key: any):
    return Mongo.delete_one({data_key: {"$exists": True}})


def disapprove_user(user_id: int):
    return Mongo.delete_one({"Approved": user_id})
