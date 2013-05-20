import md5
import psycopg2

from django.http import HttpResponse
from django.conf import settings


def get_udb_str (sql, cursor):
    '''
    Execute the given sql command and return the resulting data as a string.
    '''
    cursor.execute (sql)
    rows = cursor.fetchall()

    string = ''
    for row in rows:
        string = string + str(row)

    return string

def check_udb_for_updates (request):
    '''
    Check if any updates have been made to the userdb that may require the jasmin/cems account 
    and group information to be updated.
    '''
    
    name = request.GET.get('name', 'jasmin')

    if 'noreset' in request.GET:
        update = False
    else:
        update = True    
#
#      Make a direct connection to the database using psycopg2. I tried using django's database connection
#      but was unable to write to the database
#    
    dbsettings = settings.DATABASES['userdb']
    
    connection = psycopg2.connect(dbname=dbsettings['NAME'], 
                                  host=dbsettings['HOST'],
                                  user=dbsettings['USER'], 
                                  password=dbsettings['PASSWORD'])
 
    cursor = connection.cursor()

    sql = "select hash from update_hash where name='%s' order by id desc" % name
    cursor.execute(sql)
    rec = cursor.fetchone()
    if rec:
        stored_hash = str(rec[0])
    else:
        stored_hash = ''
    
    sql = """
    select j.id,j.userkey,j.datasetid,j.removed from tbusers,tbdatasetjoin as j, tbdatasets 
    where tbusers.userkey=j.userkey and j.datasetid = tbdatasets.datasetid 
    and tbusers.uid > 0 and tbdatasets.gid > 0;
    """

    datasetjoin_str = get_udb_str(sql, cursor)

    sql = """
    select userkey, surname, othernames, accountid, public_key, uid,
    home_directory, shell, gid 
    from tbusers
    where uid>0;
    """
    user_str = get_udb_str(sql, cursor)

    sql = """
    select datasetid, grp, gid
    from tbdatasets
    where gid>0;
    """
    
    group_str = get_udb_str(sql, cursor)

    hash_string = md5.new(datasetjoin_str + user_str + group_str).hexdigest()

    if update:
        sql = "delete from update_hash where name='%s'" % name 
        cursor.execute(sql)

        sql = "insert into update_hash (name, date, hash) values ('%s', 'now', '%s');" % (name, hash_string) 
        cursor.execute(sql)
        connection.commit()
    
    if stored_hash == hash_string:
        return HttpResponse('Same\n' + hash_string + '\n' + stored_hash, content_type="text/plain")
    else:
        return HttpResponse('Differ\n' + hash_string + '\n' + stored_hash, content_type="text/plain")
    
