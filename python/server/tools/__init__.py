from typing import Any

from .add import add
from .delete import delete
from .update import update
from .list_all import list_all

tools = {
    add["name"]: add,
    delete["name"]: delete,
    update["name"]: update,
    list_all["name"]: list_all
}

