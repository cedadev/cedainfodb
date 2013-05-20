'''
Contains routines for processing public keys
'''

def prepare_key_for_diff (key):
    '''
    Tidies up public key in order to perform comparison     
    '''    
    key = key.strip()
#    key = key.replace('\n', '')
#    key = key.replace('\r', '')
    
    key = key.replace('ssh-rsa ', '')    
    key = key.replace('ssh-dss ', '')    
    
    key = key.strip()
#
#       Cut off the 'comment' than might be at the end of the key string.
#       The comment might have spaces inside, which is why I use 'find'
#       rather than 'rfind'. 
#    
    loc = key.find(' ')
#
#       It is possible to have spaces in the key string that may
#       have originated from how the string was entered, so we only
#       accept it if it is towards the end of the string
#            
    if loc > 150:
        key = key[0:loc]
    
    key = key.rstrip('=')
    key = key.rstrip('=')

    return key



def public_keys_differ (a, b):
    '''
    Compares two public keys and returns True if they differ
    '''
    
    tidy_a = prepare_key_for_diff(a)
    tidy_b = prepare_key_for_diff(b)
            
    if tidy_a != tidy_b:
       return True
    else:
       return False  
