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


Mongo = Mongo["NiceGrill"]["Alive"]


def set_alive_name(alive_name: str):
    delete_data("Name")
    return Mongo.insert_one(
        {"Name": alive_name}
    )

def set_alive_message(alive_message: str):
    delete_data("Message")
    return Mongo.insert_one(
        {"Message": alive_message}
    )

def get_alive_name():
    if alive_name_data := Mongo.find_one({"Name": {"$exists": True}}):
        return alive_name_data["Name"]

def get_alive_message():
    if alive_message_data := Mongo.find_one({"Message": {"$exists": True}}):
        return alive_message_data["Message"]

def delete_data(data_key: any):
    Mongo.delete_one(
        {data_key: {"$exists": True}}
    )
