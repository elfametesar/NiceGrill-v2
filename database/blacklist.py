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

Mongo = Mongo["NiceGrill"]["Blacklist"]


def blacklist_chat(chat_id: int):
    whitelist_chat(chat_id)
    return Mongo.insert_one({"Blacklisted": chat_id})


def get_all_blacklisted():
    return [pair.get("Blacklisted") for pair in Mongo.find() if pair.get("Blacklisted")]


def whitelist_chat(chat_id: int):
    return Mongo.delete_one({"Blacklisted": chat_id})
