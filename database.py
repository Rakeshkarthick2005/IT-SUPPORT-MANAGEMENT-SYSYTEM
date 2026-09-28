# import mysql.connector
# connection=mysql.connector.connect(
#     host = "localhost",
#     user = "root",
#     password = "Rakesh@", 
#     database = "it_support"
# )
# print("Database Connected Sucessfully")

# cursor = connection.cursor()
# username = "petta_mani"
# password = "mani@123"
# cursor.execute(
#     "Select * from users where username = %s AND password = %s",
#     (username,password)
# )
# user = cursor.fetchone()
# if user:
#     print("Login Sucessful")
#     print("Welcome",user[1])
# else:
#     print("Invalid username or password")
import mysql.connector

connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Rakesh@",
    database="it_support"
)

print("Database Connected Successfully")

cursor = connection.cursor()

cursor.execute("SELECT id, name, username, role FROM users ORDER BY id")

for row in cursor.fetchall():
    print(row)

cursor.close()
connection.close()