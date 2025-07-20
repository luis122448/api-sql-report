# Metadata Database

This directory is intended to hold the application's metadata database.

## Database Generation

To create the empty SQLite database file, you can use the following command. The application will handle the schema initialization (tables, indexes, etc.) on its first run.

### Steps

1.  **Navigate to this directory:**

```bash
cd /path/to/your/project/data-ingestor-python/database
```

1.  **Create the empty database file:**

```bash
touch metadata.db
```

This command creates an empty `metadata.db` file, which is all that is needed for the application to start and initialize the database structure.
