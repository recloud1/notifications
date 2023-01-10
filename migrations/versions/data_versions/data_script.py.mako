"""${message}

Create Date: ${create_date}

"""

revision = ${revision}

from typing import Tuple

import sqlalchemy as sa

from .core import DataMigration, GeneratingMigration


# Please, write your values here
data: Tuple[DataMigration, ...] = ()

def data_upgrade(op):
    connection: sa.engine.Connection = op.get_bind()

    # default creation for data
    for value_set in data:
        value_set.insert(connection)


def data_downgrade(op):
    connection: sa.engine.Connection = op.get_bind()

    # default deletion for data
    for value_set in data:
        value_set.delete(connection)
