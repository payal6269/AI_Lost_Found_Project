"""
Seed sample lost & found items dataset with matched real images.
Run: python seed_dataset.py
"""
import sqlite3
from datetime import datetime, timedelta
import random

SAMPLE_ITEMS = [
    ("iPhone 13",        "Black iPhone 13 with cracked screen protector, blue case",        "Electronics", "lost",  "static|iphone.jpg"),
    ("iPhone 13 Pro",    "Found a black iPhone near canteen, has a blue cover",              "Electronics", "found", "static|iphone.jpg"),
    ("Samsung Galaxy",   "Silver Samsung phone found near library entrance",                 "Electronics", "found", "static|samsung.jpg"),
    ("Laptop Bag",       "Black laptop bag with Dell laptop inside, lost near lab 3",        "Bags",        "lost",  "static|backpack.jpg"),
    ("Black Backpack",   "Found a black backpack near computer lab, has charger inside",     "Bags",        "found", "static|backpack.jpg"),
    ("Blue Backpack",    "Blue Adidas backpack lost in cafeteria, has notebooks",            "Bags",        "lost",  "static|backpack.jpg"),
    ("AirPods",          "White Apple AirPods Pro in white case, lost in library",           "Electronics", "lost",  "static|airpods.jpg"),
    ("White Earphones",  "Found white wireless earphones near reading room",                 "Electronics", "found", "static|airpods.jpg"),
    ("Student ID Card",  "Lost student ID card, name Rahul Sharma roll 21CS045",            "Documents",   "lost",  "static|idcard.jpg"),
    ("ID Card",          "Found an ID card near main gate, belongs to CSE department",       "Documents",   "found", "static|idcard.jpg"),
    ("Car Keys",         "Lost Honda car keys with red keychain near parking lot",           "Keys",        "lost",  "static|keys.jpg"),
    ("Key Bundle",       "Found a bunch of keys near parking area, has Honda logo",          "Keys",        "found", "static|keys.jpg"),
    ("Water Bottle",     "Blue Nalgene water bottle lost in gym",                            "Other",       "lost",  "static|bottle.jpg"),
    ("Blue Bottle",      "Found a blue water bottle near sports complex",                    "Other",       "found", "static|bottle.jpg"),
    ("Spectacles",       "Black frame prescription glasses lost in classroom 204",           "Accessories", "lost",  "static|glasses.jpg"),
    ("Glasses",          "Found black spectacles on bench near block B",                     "Accessories", "found", "static|glasses.jpg"),
    ("Wallet",           "Brown leather wallet with cash and cards, lost in canteen",        "Accessories", "lost",  "static|wallet.jpg"),
    ("Brown Wallet",     "Found a brown wallet near food stall, has some cards",             "Accessories", "found", "static|wallet.jpg"),
    ("Calculator",       "Casio scientific calculator lost during exam in hall 1",           "Electronics", "lost",  "static|calculator.jpg"),
    ("Casio Calculator", "Found a scientific calculator in examination hall",                "Electronics", "found", "static|calculator.jpg"),
    ("Umbrella",         "Printed umbrella lost near main entrance",                         "Other",       "lost",  "static|umbrella.jpg"),
    ("Black Umbrella",   "Found umbrella near security cabin",                               "Other",       "found", "static|umbrella.jpg"),
    ("Notebook",         "Black notebook with Physics notes, lost in lab",                   "Documents",   "lost",  "static|notebook.jpg"),
    ("Red Notebook",     "Found a notebook near physics lab",                                "Documents",   "found", "static|notebook.jpg"),
    ("Headphones",       "boAt Rockerz black headphones lost in library",                    "Electronics", "lost",  "static|headphones.jpg"),
    ("Sony Headphones",  "Found black over-ear headphones near study area",                  "Electronics", "found", "static|headphones.jpg"),
    ("Jacket",           "Navy blue hoodie jacket lost in seminar hall",                     "Clothing",    "lost",  "static|hoodie.jpg"),
    ("Blue Hoodie",      "Found a navy blue jacket on chair in auditorium",                  "Clothing",    "found", "static|hoodie.jpg"),
    ("Pen Drive",        "32GB SanDisk pen drive lost, has important project files",         "Electronics", "lost",  "static|pendrive.jpg"),
    ("USB Drive",        "Found a SanDisk USB drive near computer lab 2",                    "Electronics", "found", "static|pendrive.jpg"),
]


def seed():
    conn = sqlite3.connect('database.db')
    conn.execute("DELETE FROM items WHERE reported_by='system'")
    conn.commit()

    base_date = datetime(2026, 1, 1)
    for name, desc, cat, itype, image_data in SAMPLE_ITEMS:
        dt = base_date + timedelta(days=random.randint(0, 80))
        conn.execute(
            '''INSERT INTO items
               (name, description, category, type, image_data, reported_by, phone, email, reported_at, status)
               VALUES (?,?,?,?,?,?,?,?,?,?)''',
            (name, desc, cat, itype, image_data, 'system', '', '',
             dt.strftime('%Y-%m-%d %H:%M'), 'active')
        )

    conn.commit()
    conn.close()
    print(f"Seeded {len(SAMPLE_ITEMS)} items with matched images.")


if __name__ == '__main__':
    seed()
