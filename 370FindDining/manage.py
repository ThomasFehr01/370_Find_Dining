#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import sqlite3


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FindDining.settings')

    # Initialize database if not already setup
    if not os.path.exists("FindDining.db"):
        con = sqlite3.connect("FindDining.db")
        cur = con.cursor()

        cur.execute("CREATE TABLE users (user_id text, location text, rel_places text,"
                    " cur_rel_places text, prev_rel_places text)")
        cur.execute("CREATE TABLE places (place_id text, name text, rating text, num_ratings text, "
                    "price text, geolocation text, address text, type text, tags text, photo_ref text,"
                    "phone text, map_url text, website text, open text)")
        con.commit()

        con.close()

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
