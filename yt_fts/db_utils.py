import sqlite3

from sqlite_utils import Database
from tabulate import tabulate

from yt_fts.utils import show_message
from yt_fts.config import get_db_path 


def make_db(db_path):
    db = Database(db_path)

    db["Channels"].create({
            "channel_id": str,
            "channel_name": str,
            "channel_url": str,
        }, 
        pk="channel_id", 
        not_null={"channel_name", "channel_url"}, 
        if_not_exists=True
    )

    db["Videos"].create({
            "video_id": str,
            "video_title": str,
            "video_url": str,
            "channel_id": str
        }, 
        pk="video_id", 
        not_null={"video_title", "video_url"}, 
        if_not_exists=True, 
        foreign_keys=[
            ("channel_id", "Channels")
        ]
    )

    db["Subtitles"].create(
        {
            "subtitle_id": int,
            "video_id": str,
            "timestamp": str,
            "text": str
        }, 
        pk="subtitle_id", 
        not_null={"timestamp", "text"}, 
        if_not_exists=True, 
        foreign_keys=[
            ("video_id", "Videos")
        ]
    ).enable_fts(
        ["text"], 
        create_triggers=True, 
        replace=True
    )

    db["Embeddings"].create(
        {
            "subtitle_id": int,
            "video_id": str,
            "timestamp": str,
            "text": str,
            "embeddings": bytes
        },
        pk="subtitle_id", 
        not_null={"timestamp", "text"}, 
        if_not_exists=True, 
        foreign_keys=[
            ("video_id", "Videos")
        ]
    )

    db["SemanticSearchHist"].create(
        {
            "search_str": str,
            "embeddings": bytes
        },
        pk="search_str",
        not_null={"embeddings"},
        if_not_exists=True
    )

    db["SemanticSearchEnabled"].create(
        {
            "channel_id": str,
        },
        if_not_exists=True,
        foreign_keys=[
            ("channel_id", "Channels")
        ]
        
    )


def add_channel_info(channel_id, channel_name, channel_url):
    
    db = Database(get_db_path())

    db["Channels"].insert({
        "channel_id": channel_id,
        "channel_name": channel_name,
        "channel_url": channel_url
    })


def add_video(channel_id, video_id,  video_title, video_url):
    
    db = Database(get_db_path())

    db["Videos"].insert({
        "video_id": video_id,
        "video_title": video_title,
        "video_url": video_url,
        "channel_id": channel_id
    })


def add_subtitle(video_id, start_time, text):
    
    db = Database(get_db_path())

    db["Subtitles"].insert({
        "video_id": video_id,
        "timestamp": start_time,
        "text": text
    })


def get_channels():
    
    db = Database(get_db_path())

    return db.execute("SELECT ROWID, channel_id, channel_name, channel_url FROM Channels").fetchall()


def search_channel(channel_id, text):
    
    db = Database(get_db_path())

    return list(db["Subtitles"].search(text, where=f"video_id IN (SELECT video_id FROM Videos WHERE channel_id = '{channel_id}')"))


def search_video(video_id, text):
    
    db = Database(get_db_path())

    return list(db["Subtitles"].search(text, where=f"video_id = '{video_id}'"))

def search_all(text):
    
    db = Database(get_db_path())

    return list(db["Subtitles"].search(text))


def get_title_from_db(video_id):

    db = Database(get_db_path())

    return db.execute(f"SELECT video_title FROM Videos WHERE video_id = ?", [video_id]).fetchone()[0]


def get_channel_name_from_id(channel_id):
    
    db = Database(get_db_path())

    return db.execute(f"SELECT channel_name FROM Channels WHERE channel_id = ?", [channel_id]).fetchone()[0]

def get_channel_name_from_video_id(video_id):
    
    db = Database(get_db_path())

    return db.execute(f"SELECT channel_name FROM Channels WHERE channel_id = (SELECT channel_id FROM Videos WHERE video_id = ?)", [video_id]).fetchone()[0]


# delete all videos, subtitles, and embeddings associated with channel
def delete_channel(channel_id):
    
    conn = sqlite3.connect(get_db_path())
    cur = conn.cursor()

    cur.execute("DELETE FROM Channels WHERE channel_id = ?", (channel_id,))

    # make sure to delete all subtitles and embeddings before videos  
    cur.execute("DELETE FROM Subtitles WHERE video_id IN (SELECT video_id FROM Videos WHERE channel_id = ?)", (channel_id,))
    cur.execute("DELETE FROM Embeddings WHERE video_id IN (SELECT video_id FROM Videos WHERE channel_id = ?)", (channel_id,))

    cur.execute("DELETE FROM Videos WHERE channel_id = ?", (channel_id,))
    cur.execute("DELETE FROM SemanticSearchEnabled WHERE channel_id = ?", (channel_id,))

    conn.commit()
    conn.close()


def get_channel_id_from_rowid(rowid):
    
    db = Database(get_db_path())

    res = db.execute(f"SELECT channel_id FROM Channels WHERE ROWID = ?", [rowid]).fetchone()

    if res is None:
        return None
    else:
        return res[0]


def get_channel_id_from_name(channel_name):
    
    db = Database(get_db_path())

    res = db.execute(f"SELECT channel_id FROM Channels WHERE channel_name = ?", [channel_name]).fetchall()

    if len(res) > 1:
        channels = db.execute(f"SELECT ROWID, channel_name, channel_url FROM Channels WHERE channel_name = ?", [channel_name]).fetchall()
        print(tabulate(channels, headers=["id", "channel_name", "channel_url"]))
        print("")
        show_message("multiple_channels_found")
        exit()
    if len(res) == 0:
        return None
    else:
        return res[0][0]


# for listing specific channel 
def get_channel_list_by_id(channel_id):
    
    db = Database(get_db_path())

    return db.execute(f"SELECT ROWID, channel_name, channel_url FROM Channels WHERE channel_id = ?", [channel_id]).fetchall()


def check_if_channel_exists(channel_id):

    db = Database(get_db_path())

    res = db.execute(f"SELECT channel_id FROM Channels WHERE channel_id = ?", [channel_id]).fetchall()
    if len(res) > 0:
        return True
    else:
        return False

def get_num_vids(channel_id):
    
    db = Database(get_db_path())

    return db.execute(f"SELECT COUNT(*) FROM Videos WHERE channel_id = ?", [channel_id]).fetchone()[0]

def get_vid_ids_by_channel_id(channel_id):
    
    db = Database(get_db_path())

    return db.execute(f"SELECT video_id FROM Videos WHERE channel_id = ?", [channel_id]).fetchall()


def get_all_subs_by_channel_id(channel_id):
    
    db = Database(get_db_path())

    parsed_subs = []
    subs = db.execute("""
        SELECT s.subtitle_id, s.video_id, s.timestamp, s.text 
        FROM Subtitles s
        JOIN Videos v ON s.video_id = v.video_id
        WHERE v.channel_id = ?
        """, [channel_id]).fetchall()
    
    for sub in subs:
        if len(sub[3].strip()) > 0:
            parsed_subs.append(sub)
    return parsed_subs

# get all subs where semantic search is enabled
def get_all_subs_by_channel_id_ss(channel_id):
    
    db = Database(get_db_path())

    parsed_subs = []
    subs = db.execute("""
        SELECT s.subtitle_id, s.video_id, s.timestamp, s.text 
        FROM Subtitles s
        JOIN Videos v ON s.video_id = v.video_id
        WHERE v.channel_id = ?
        """, [channel_id]).fetchall()
    
    for sub in subs:
        if len(sub[3].strip()) > 0:
            parsed_subs.append(sub)
    return parsed_subs