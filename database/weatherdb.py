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

Mongo = Mongo["NiceGrill"]["Weather"]


def set_city_name(city_name: str):
    delete_data("City")
    return Mongo.insert_one(
        {"City": city_name}
    )

def get_city_name():
    if city_name_data := Mongo.find_one({"City": {"$exists": True}}):
        return city_name_data["City"]

def delete_data(data_key: any):
    return Mongo.delete_one(
        {data_key: {"$exists": True}}
    )
        
