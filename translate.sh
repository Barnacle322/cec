pybabel extract -F babel.cfg -o messages.pot .
pybabel update -i messages.pot -d src/project/translations
pybabel compile -d src/project/translations