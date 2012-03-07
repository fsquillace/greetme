import pickle, os

def visits():
    path = 'visits.txt'
    c=0
    if os.path.exists(path):
        c = pickle.load(open(path, 'rb'))
    c+=1
    pickle.dump(c, open(path, 'wb'))
    return c

