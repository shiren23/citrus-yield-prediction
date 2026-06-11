"""
柑橘产量预测系统 - SQLite 数据库操作模块
管理果园信息、检测记录和历史产量数据
"""

import os
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple

from core.config import DB_PATH


class CitrusDatabase:
    """柑橘产量预测数据库"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_tables()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        """初始化数据库表结构"""
        conn = self._connect()
        cursor = conn.cursor()

        # 果园/树木基本信息表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orchard_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                variety TEXT DEFAULT '通用柑橘',
                tree_count INTEGER DEFAULT 1,
                location TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 检测记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detection_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                orchard_id INTEGER,
                image_path TEXT,
                stage TEXT,
                flower_count INTEGER DEFAULT 0,
                immature_count INTEGER DEFAULT 0,
                mature_count INTEGER DEFAULT 0,
                predicted_yield REAL,
                confidence REAL,
                risk_level TEXT,
                risk_ratio REAL,
                variety TEXT,
                detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (orchard_id) REFERENCES orchard_info(id)
            )
        """)

        # 历史实际产量表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS history_yield (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                orchard_id INTEGER,
                year INTEGER,
                season TEXT,
                actual_yield REAL,
                recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (orchard_id) REFERENCES orchard_info(id)
            )
        """)

        self._migrate_columns(cursor)
        conn.commit()
        conn.close()
        print(f"[Database] 数据库已初始化: {self.db_path}")

    def _migrate_columns(self, cursor):
        """增量添加新列，兼容已有数据库"""
        migrations = [
            ("history_yield", "detection_id", "INTEGER"),
            ("history_yield", "harvest_date", "TEXT"),
            ("history_yield", "per_tree_yield", "REAL"),
        ]
        for table, column, col_type in migrations:
            try:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
            except sqlite3.OperationalError:
                pass

    # ---------- 果园信息操作 ----------

    def add_orchard(self, name: str, variety: str = "通用柑橘",
                    tree_count: int = 1, location: str = "") -> int:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO orchard_info (name, variety, tree_count, location) VALUES (?, ?, ?, ?)",
            (name, variety, tree_count, location)
        )
        orchard_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return orchard_id

    def get_orchard(self, orchard_id: int) -> Optional[Dict]:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orchard_info WHERE id = ?", (orchard_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def list_orchards(self) -> List[Dict]:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orchard_info ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def update_orchard(self, orchard_id: int, **kwargs) -> bool:
        allowed = {"name", "variety", "tree_count", "location"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return False
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [orchard_id]
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(f"UPDATE orchard_info SET {set_clause} WHERE id = ?", values)
        conn.commit()
        conn.close()
        return True

    def delete_orchard(self, orchard_id: int) -> bool:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM orchard_info WHERE id = ?", (orchard_id,))
        conn.commit()
        conn.close()
        return True

    # ---------- 检测记录操作 ----------

    def add_detection(self, orchard_id: int, counts: Dict[str, int],
                      stage: str, predicted_yield: float,
                      confidence: float, risk_level: str,
                      risk_ratio: float, variety: str,
                      image_path: str = "") -> int:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO detection_records
            (orchard_id, image_path, stage, flower_count, immature_count, mature_count,
             predicted_yield, confidence, risk_level, risk_ratio, variety)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            orchard_id, image_path, stage,
            counts.get("flower", 0),
            counts.get("immature_fruit", 0),
            counts.get("mature_fruit", 0),
            predicted_yield, confidence, risk_level, risk_ratio, variety
        ))
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return record_id

    def get_detections(self, orchard_id: Optional[int] = None,
                       limit: int = 100) -> List[Dict]:
        conn = self._connect()
        cursor = conn.cursor()
        if orchard_id is not None:
            cursor.execute(
                "SELECT * FROM detection_records WHERE orchard_id = ? ORDER BY detected_at DESC LIMIT ?",
                (orchard_id, limit)
            )
        else:
            cursor.execute(
                "SELECT * FROM detection_records ORDER BY detected_at DESC LIMIT ?",
                (limit,)
            )
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_detection_counts_history(self, orchard_id: int) -> List[Dict]:
        """获取某果园的历史检测数量记录"""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT stage, flower_count, immature_count, mature_count, detected_at
            FROM detection_records
            WHERE orchard_id = ?
            ORDER BY detected_at ASC
        """, (orchard_id,))
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                "stage": r["stage"],
                "counts": {
                    "flower": r["flower_count"],
                    "immature_fruit": r["immature_count"],
                    "mature_fruit": r["mature_count"],
                },
                "detected_at": r["detected_at"],
            }
            for r in rows
        ]

    # ---------- 历史产量操作 ----------

    def add_history_yield(self, orchard_id: int, year: int,
                          season: str, actual_yield: float,
                          detection_id: Optional[int] = None,
                          harvest_date: str = "",
                          per_tree_yield: Optional[float] = None) -> int:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO history_yield
               (orchard_id, year, season, actual_yield, detection_id, harvest_date, per_tree_yield)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (orchard_id, year, season, actual_yield, detection_id, harvest_date, per_tree_yield)
        )
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return record_id

    def get_detection(self, detection_id: int) -> Optional[Dict]:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM detection_records WHERE id = ?", (detection_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_detections_with_orchard(self, orchard_id: Optional[int] = None,
                                    limit: int = 200) -> List[Dict]:
        conn = self._connect()
        cursor = conn.cursor()
        sql = """
            SELECT d.*, o.name AS orchard_name
            FROM detection_records d
            LEFT JOIN orchard_info o ON d.orchard_id = o.id
        """
        params: Tuple = ()
        if orchard_id is not None:
            sql += " WHERE d.orchard_id = ?"
            params = (orchard_id,)
        sql += " ORDER BY d.detected_at DESC LIMIT ?"
        params = params + (limit,)
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def delete_detection(self, detection_id: int) -> bool:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM detection_records WHERE id = ?", (detection_id,))
        conn.commit()
        conn.close()
        return True

    def get_history_yields(self, orchard_id: int) -> List[Dict]:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM history_yield WHERE orchard_id = ? ORDER BY year DESC, season DESC",
            (orchard_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ---------- 统计与报告 ----------

    def get_yield_trend(self, orchard_id: int) -> List[Dict]:
        """获取产量预测趋势"""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT predicted_yield, detected_at, stage, risk_level
            FROM detection_records
            WHERE orchard_id = ?
            ORDER BY detected_at ASC
        """, (orchard_id,))
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                "predicted_yield": r["predicted_yield"],
                "detected_at": r["detected_at"],
                "stage": r["stage"],
                "risk_level": r["risk_level"],
            }
            for r in rows
        ]

    def export_to_csv(self, orchard_id: Optional[int] = None) -> str:
        """导出检测记录为CSV字符串"""
        import io
        import csv
        records = self.get_detections(orchard_id, limit=10000)
        if not records:
            return ""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
        return output.getvalue()


# 单例
_db_instance: Optional[CitrusDatabase] = None


def get_db() -> CitrusDatabase:
    global _db_instance
    if _db_instance is None:
        _db_instance = CitrusDatabase()
    return _db_instance
