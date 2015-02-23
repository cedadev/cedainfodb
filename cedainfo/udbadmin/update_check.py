'''
Contains routines for checking if the user database has been updated.
'''

import md5

def get_udb_str (sql, cursor):
    '''
    Execute the given sql command and return the resulting data as a string.
    '''
    cursor.execute (sql)
    rows = cursor.fetchall()

    string = str(rows)

    return string     
    
    
def user_updated (connection, reset=True, name='jasmin_user'):
    '''
    Check if any updates have been made to the userdb that may require LDAP
    user information to be updated
    '''

    cursor = connection.cursor()

    sql = "select hash from update_hash where name='%s' order by id desc" % name
    cursor.execute(sql)
    rec = cursor.fetchone()
    if rec:
        stored_hash = str(rec[0])
    else:
        stored_hash = ''
    
    sql = """
    select userkey, accountid, public_key, uid, encpasswd,
    home_directory, shell, gid, surname, othernames 
    from tbusers
    where uid>0;
    """
    user_str = get_udb_str(sql, cursor)
    hash_string = md5.new(user_str).hexdigest()
        
    if stored_hash == hash_string:
        return False
    else:
        if reset:
            sql = "delete from update_hash where name='%s'" % name 
            cursor.execute(sql)

            sql = """insert into update_hash (name, date, hash) 
                     values ('%s', 'now', '%s');""" % (name, hash_string) 
            cursor.execute(sql)
            connection.commit()
 
        return True    

def group_updated (connection, reset=True, name='jasmin_group'):
    '''
    Check if any updates have been made to the userdb that may require LDAP
    group information to be updated
    '''

    cursor = connection.cursor()

    sql = "select hash from update_hash where name='%s' order by id desc" % name
    cursor.execute(sql)
    rec = cursor.fetchone()

    if rec:
        stored_hash = str(rec[0])
    else:
        stored_hash = ''
    
    sql = """
    select j.id,j.userkey,j.datasetid,j.removed from tbusers,tbdatasetjoin as j
    where tbusers.userkey=j.userkey
    and tbusers.uid > 0;
    """

    datasetjoin_str = get_udb_str(sql, cursor)

    sql = """
    select datasetid, grp, gid
    from tbdatasets
    where gid>0;
    """
    
    group_str = get_udb_str(sql, cursor)

    hash_string = md5.new(datasetjoin_str + group_str).hexdigest()
        
    if stored_hash == hash_string:
        return False
    else:
        if reset:
            sql = "delete from update_hash where name='%s'" % name 
            cursor.execute(sql)

            sql = """insert into update_hash (name, date, hash) 
                     values ('%s', 'now', '%s');""" % (name, hash_string) 
            cursor.execute(sql)
            connection.commit()
    
        return True    

