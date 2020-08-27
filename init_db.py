import os

import config_app
from app import db, User, Categories


def add_category(little_name, real_name, parent=1, isactive=True):
    father = Categories.query.filter_by(idg=parent).first()
    categories = Categories.query.all()
    for c in categories:
        if c.idg > father.idg: c.idg += 2
        if c.idd > father.idg: c.idd += 2
        if c.parent != None and c.parent > father.idg: c.parent += 2
        db.session.commit()
    db.session.add(
        Categories(little_name=little_name, real_name=real_name, parent=parent, idg=parent + 1, idd=parent + 2,
                   isactive=isactive))
    db.session.commit()


def find_children(idg):
    return Categories.query.filter_by(parent=idg).order_by(Categories.idg).all()


##Main###
print("Creating and adding admin...")
if os.path.exists('static/zonensidb.sqlite3'):
    os.remove('static/zonensidb.sqlite3')
db.create_all()
user = User(login=config_app.ADMIN_LOGIN, password=config_app.ADMIN_PWD)
db.session.add(user)
db.session.commit()
racine = Categories(little_name='root', real_name='Root', parent=None, idg=1, idd=2)
db.session.add(racine)

db.session.commit()
print("Done !")

print("Creating and adding Top categories...")

course = [('maths', 'Mathématiques'), ('snt', 'SNT'), ('nsi', 'NSI'), ('enssci', 'Enseignement Scientifique'),
          ('misc', 'Miscellanées')]

for ln, rn in course[::-1]:
    add_category(ln, rn)
    if not (os.path.exists(f"static/upload/{ln}")):
        try:
            os.mkdir(f"static/upload/{ln}")
        except:
            raise IOError
print("Done !")

print("Creating and adding Maths sub categories...")
num = Categories.query.filter_by(little_name="maths").first().idg
cat = [('2de', 'Seconde'), ('1ereG', 'Première Générale'), ('TleG', 'Terminale Générale'),
       ('1ereT', 'Première Technologique'),
       ('TleT', 'Terminale Technologique'), ('mathexp', 'Maths Expertes'), ('mathcomp', 'Maths Complémentaires'),
       ('cultmath', 'Culture Mathématique')]
for ln, rn in cat[::-1]:
    add_category(ln, rn, parent=num)
    if not (os.path.exists(f"static/upload/maths/{ln}")):
        try:
            os.mkdir(f"static/upload/maths/{ln}")
        except:
            raise IOError
print("Creating and adding NSI sub categories...")

num = Categories.query.filter_by(little_name="nsi").first().idg
cat = [('1ereG', 'Première Générale'), ('TleG', 'Terminale Générale'), ('cultinfo', 'Culture Informatique')]
for ln, rn in cat[::-1]:
    add_category(ln, rn, parent=num)
    if not (os.path.exists(f"static/upload/nsi/{ln}")):
        try:
            os.mkdir(f"static/upload/nsi/{ln}")
        except:
            raise IOError

print("Creating and adding MISC sub categories...")

num = Categories.query.filter_by(little_name="misc").first().idg
cat = [('python', 'Python'), ('web', 'Web'), ('reseaux', 'Réseaux'), ('linux', 'Linux')]
for ln, rn in cat[::-1]:
    add_category(ln, rn, parent=num)
    if not (os.path.exists(f"static/upload/misc/{ln}")):
        try:
            os.mkdir(f"static/upload/misc/{ln}")
        except:
            raise IOError

print("Creating and adding sub-sub categories...")

for parent, course in [('maths', '2de'), ('maths', 'mathcomp'), (None, 'snt'), (None, 'enssci'), ('nsi', '1ereG')]:
    if parent != None:
        parent_idg = Categories.query.filter_by(little_name=parent).first().idg
        num = Categories.query.filter_by(little_name=course, parent=parent_idg).first().idg
        # Création des différents chapitres
        cat = [(f'C{i // 10}{i % 10}',) * 2 for i in range(1, 16)]
        for ln, rn in cat[::-1]:
            add_category(ln, rn, parent=num, isactive=(ln == 'C01'))
            if not (os.path.exists(f"static/upload/{parent}/{course}/{ln}")):
                try:
                    os.mkdir(f"static/upload/{parent}/{course}/{ln}")
                except:
                    raise IOError
    else:
        num = Categories.query.filter_by(little_name=course).first().idg
        # Création des différents chapitres
        cat = [(f'C{i // 10}{i % 10}',) * 2 for i in range(1, 16)]
        for ln, rn in cat[::-1]:
            add_category(ln, rn, parent=num, isactive=(ln == 'C01'))
            if not (os.path.exists(f"static/upload/{course}/{ln}")):
                try:
                    os.mkdir(f"static/upload/{course}/{ln}")
                except:
                    raise IOError
    print(f'Done for {parent}/f{course}...')

print('Finished')

db.close_all_sessions()
