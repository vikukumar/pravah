"""Apply missing column additions for workflow versioning migration."""
from sqlalchemy import create_engine, text, inspect

engine = create_engine("sqlite:///./pravah.db")

NEW_COLUMNS = {
    "workflows": [
        ("published_version", "INTEGER"),
        ("tags", "TEXT"),
        ("icon", "VARCHAR(100)"),
        ("color", "VARCHAR(20)"),
        ("notes", "TEXT"),
        ("requires_approval", "BOOLEAN DEFAULT 0"),
        ("approval_mode", "VARCHAR(50)"),
        ("last_execution_status", "VARCHAR(50)"),
    ],
    "workflow_executions": [
        ("workflow_version", "INTEGER"),
        ("trigger_payload", "TEXT"),
        ("queued_at", "DATETIME"),
        ("retry_count", "INTEGER DEFAULT 0"),
    ],
    "workflow_nodes": [
        ("label", "VARCHAR(200)"),
        ("color", "VARCHAR(20)"),
        ("notes", "TEXT"),
    ],
    "workflow_node_executions": [
        ("retry_count", "INTEGER DEFAULT 0"),
    ],
    "workflow_edges": [
        ("edge_type", "VARCHAR(50)"),
    ],
}

with engine.connect() as conn:
    insp = inspect(engine)
    for table, cols in NEW_COLUMNS.items():
        existing = {c["name"] for c in insp.get_columns(table)}
        for col_name, col_def in cols:
            if col_name not in existing:
                sql = f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def}"
                conn.execute(text(sql))
                print(f"Added {table}.{col_name}")
            else:
                print(f"Skip {table}.{col_name} (exists)")
    conn.commit()

print("Migration column additions complete.")
