import sqlite3

if __name__ == '__main__':
    connect = sqlite3.connect('D:\\ML_B_Website\\spotify_site\\spotify_site\\discoverify\\user_info.db')
    """cursor = connect.execute('''
                            SELECT *
                            FROM user_info
                            WHERE user_id = "thatboihaxor48"; 
                            ''')
    print(cursor.fetchone())
    cursor.close()"""
    connect.execute('''
                   DELETE
                   FROM user_info
                   WHERE user_id = "thatboihaxor48";
                   ''')
    connect.commit()
    connect.close()
    