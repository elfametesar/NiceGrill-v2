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


Mongo = Mongo["NiceGrill"]["Snippets"]


def save_snip(snippet_name: str, snippet_value):
    delete_data(f"SavedSnippet.{snippet_name}")
    return Mongo.insert_one(
        {
            "SavedSnippet": {
                snippet_name: snippet_value
            }
        }
    )

def allow_others(option: bool):
    delete_data("Others")
    return Mongo.insert_one(
        {"Others": option}
    )

def is_others_allowed():
    if snippet_name_data := Mongo.find_one({"Others": {"$exists": True}}):
        return snippet_name_data["Others"]

def get_snip(snippet_name: str):
    if snippet_name_data := Mongo.find_one({snippet_name: {"$exists": True}}):
        return snippet_name_data[snippet_name]

def get_all_snips():
    saved_snippets = {}
    [saved_snippets.update(pair.get("SavedSnippet")) for pair in Mongo.find() if pair.get("SavedSnippet")]
    return saved_snippets

def delete_data(data_key: any):
    Mongo.delete_one(
        {data_key: {"$exists": True}}
    )
