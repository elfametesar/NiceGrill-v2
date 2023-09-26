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

Mongo = Mongo["NiceGrill"]["Quote"]


def set_message_color(color: str|tuple):
    delete_data("Message Box Color")
    return Mongo.insert_one(
        {"Message Box Color": color}
    )

def get_message_color():
    if message_box_data := Mongo.find_one({"Message Box Color": {"$exists": True}}):
        if isinstance(message_box_data["Message Box Color"], list):
            r,g,b,a = message_box_data["Message Box Color"]
            return r,g,b,a
        else:
            return message_box_data["Message Box Color"]

def delete_data(data_key: any):
    return Mongo.delete_one(
        {data_key: {"$exists": True}}
    )
        
