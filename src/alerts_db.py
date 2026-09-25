import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(_file_).resolve().parent / "watchlist.db"

def init_alerts_db():
  with sqlite3.connect(DB_PATH) as connection:
    connection.execute(
      """
      CREATE TABLE IF NOT EXISTS alerts (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      symbol TEXT NOT NULL,
      condition_type TEXT NOT NULL,
      target_value REAL NOT NULL,
      enabled INTEGER NOT NULL DEFAULT 1,
      created_at TEXT NOT NULL
       )
      """
    )
    connection.commit()

    def add_alert(symbol, condition_type, target_value):
      with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
          """
          INSERT INTO alerts
          (symbol,condition_type,target_value,enabled,created_at)
          VALUES (?, ?, ?, 1, ?)
          """,
          (
            symbol.upper(),
            condition_type,
            float(target_value),
            datetime.now().isoformat(timespec="seconds"),

          ),
        )
        connection.commit()

        def get_alerts():
          with sqlite3.connect(DB_PATH) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
              """
              SELECT id, symbol, condition_type, target_value,
                 enabled, created_at

                 FROM alerts
                 ORDER BY id DESC
                 """
                 ).fetchall()

                 return [dict(row) for row in rows]


                 def set_alert_enabled(alert_id, enabled):
                  with sqlite3.connect(DB_PATH) as connection:
                    connection.execute(

                       "UPDATE alerts SET enabled = ? WHERE id = ?",
                       (1 if enabled else 0, alert_id),
                    )

                    connection.commit()


                    def delete_alert(alert_id):
                      with sqlite3.connect(DB_PATH) as connection:
                        connection.execute(
                          "DELETE FROM alerts WHERE id = ?",
                          (alert_id,),
                        )

                        connection.commit()



