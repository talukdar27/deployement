import os
import psycopg2

conn = psycopg2.connect("postgresql://runtimeerror:76mHyzfr9k_rqrgRFhHQ8A@run-time-error-4066.7s5.aws-ap-south-1.cockroachlabs.cloud:26257/ChitrKatha?sslmode=verify-full")
cursor=conn.cursor()
cursor.execute("SELECT now()")
result=cursor.fetchall()
conn.commit()
print(result)
