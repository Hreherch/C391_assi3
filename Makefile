all: A3.db
	echo Made all
A3.db: dbMake.txt
	sqlite3 A3.db < dbMake.txt

clean:
	rm -f A3.db