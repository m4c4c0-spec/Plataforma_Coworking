# MariaDB ejecuta este archivo solo al crear el volumen por primera vez.
# Permite al usuario de la aplicación crear la base temporal de `manage.py test`.
docker_process_sql --database=mysql <<-EOSQL
	GRANT ALL PRIVILEGES ON \`test_${MARIADB_DATABASE}\`.* TO '${MARIADB_USER}'@'%';
EOSQL
