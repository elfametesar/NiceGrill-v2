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

Mongo = Mongo["NiceGrill"]["Settings"]


def set_download_path(download_path: str):
    delete_data("Download Path")
    return Mongo.insert_one(
        {"Download Path": download_path}
    )

def set_shell_mode(switch: bool):
    delete_data("Shell Mode")
    return Mongo.insert_one(
        {"Shell Mode": switch}
    )

def set_prefix(new_prefix: str):
    delete_data("Prefix")
    return Mongo.insert_one(
        {"Prefix": new_prefix}
    )

def set_restart_details(chat_id: int, message_id: int):
    delete_data("Message")
    return Mongo.insert_one(
        {
            "Chat": chat_id,
            "Message": message_id
        }
    )

def get_download_path():
    if download_path_data := Mongo.find_one({"Download Path": {"$exists": True}}):
        return download_path_data["Download Path"]

def is_shell():
    if shell_mode_data := Mongo.find_one({"Shell Mode": {"$exists": True}}):
        return shell_mode_data["Shell Mode"]

def get_prefix():
    if prefix_data := Mongo.find_one({"Prefix": {"$exists": True}}):
        return prefix_data["Prefix"]

def get_restart_details():
    if restart_data := Mongo.find_one({"Message": {"$exists": True}}):
        return restart_data

def delete_data(data_key: any):
    return Mongo.delete_one(
        {data_key: {"$exists": True}}
    )


